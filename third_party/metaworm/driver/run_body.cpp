// Headless driver for the MetaWorm (BAAIWorm) body. Our code; upstream sim/ is unchanged apart from the marked wormemu extension in sim/fem/World.h/.cpp (UPSTREAM.md).
// It replaces only the interface: the GLUT window loop (render/SimulationWindow.cpp Timer) and the Boost.Python
// bridge (interact/). The stepping matches the published loop: muscle input set at the control rate (30 Hz),
// then SimulationHz/ControlHz = 8 physics steps (240 Hz), each Environment::Step() = drag forces + one
// projective-dynamics step.
//
// Modes
//   key   published built-in gait: Environment::SetActions(zero normalised actions) each control step, so the head
//         segment of each of the 4 fibre muscles follows the key csv (one row per control step, looping) and the
//         activation is transported tailward by Muscle::SetActivationLevels (alpha 0.3, 2 sub-steps).
//   wave  our prescribed travelling wave through Worm::SetActivationLevelsDirectly (96 values, 4 muscles x 24
//         segments, head first): dorsal a = amp (1 + sin phi)/2, ventral a = amp (1 - sin phi)/2,
//         phi = 2 pi (f t - s / lam), s = (j + 0.5)/24, ramped in over the first period.
//   dead  all 96 activations 0.
//   pipe  closed loop (our code): the caller sends, per exchange, int32 n_steps, int32 flags (bit 0: dump a frame
//         after the steps), then 96 float64 activations (Worm::SetActivationLevelsDirectly order, held for the
//         n_steps physics steps); the driver replies with 3 n_vertices float64 positions. n_steps <= 0 ends the
//         run. Before the first exchange it writes int32 n_vertices, int32 n_act, float64 physics dt and the rest
//         positions. Pipes: --fd_in, --fd_out (file descriptors passed by the caller; stdout carries upstream's
//         log). P.json is written at the start too, so the caller can read the mesh metadata.
//   --solver_exit published|latest (toggle body.solver_exit, neutral published): on convergence, return the
//         iterate before the converged solve (upstream) or the converged solve itself (World extension).
//   --release_at T (key, wave, dead): from time T on, all 96 activations are 0.
//
// Worm-scale world (our code; toggles body.scale, env.fluid, env.substrate; the defaults are the published world
// and leave that code unused, so P0/P2 are unchanged):
//   --scale published|worm_1mm   worm_1mm: 1 length unit = 1 mm / rest length (body 1.0 mm), mass unit chosen so
//         stress and drag per length are numerically SI; mass = 1074 kg/m^3 x mesh volume, spread evenly.
//   --fluid quadratic_published|agar_rft|viscous_rft_water   RFT: linear drag w [c_t t t^T + c_n (I - t t^T)] per
//         vertex in the implicit solve (World::SetDragMatrix), t from 24 slice centroids, rebuilt every
//         --drag_every physics steps; c_t, c_n in Pa s (agar 3.2 / 128, BBC 2012; water 0.00357 / 0.005675),
//         overridable with --ct, --cn. RFT replaces the published quadratic drag (Environment::Step is bypassed).
//   --substrate none_published|agar_plate|agar_film, --side_down right|left   gravity 9.81 m/s^2 toward the plate;
//         the plate plane touches the rest body's lowest point; after each step, vertices below it are put back on
//         it and their velocity into it zeroed. agar_film adds the water film's surface as a second wall at the
//         rest body's thickness above the plate, same rule (the meniscus as a hard wall, BODY_TESTS.md).
//
// Output (prefix P): P.frames.f32 float32 [n_frames, n_vertices, 3] world positions, frame 0 = rest pose;
//                    P.act.f32 float32 [n_frames, 96]; P.json metadata (surface triangles, muscle names, rest
//                    segment endpoints, run parameters, wall time).
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <unistd.h>
#include <Eigen/Core>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include "Environment.h"

static const char* arg(int argc, char** argv, const char* name, const char* dflt)
{
	for (int i = 1; i + 1 < argc; i++)
		if (!std::strcmp(argv[i], name)) return argv[i + 1];
	return dflt;
}

int main(int argc, char** argv)
{
	std::string mode = arg(argc, argv, "--mode", "key");
	std::string key = arg(argc, argv, "--key", "");
	double seconds = std::atof(arg(argc, argv, "--seconds", "10"));
	double f = std::atof(arg(argc, argv, "--f", "1.76"));
	double lam = std::atof(arg(argc, argv, "--lam", "1.54"));
	double amp = std::atof(arg(argc, argv, "--amp", "0.03"));
	int frame_every = std::atoi(arg(argc, argv, "--frame_every", "1"));
	double release_at = std::atof(arg(argc, argv, "--release_at", "1e30"));
	std::string out = arg(argc, argv, "--out", "run");
	std::string solver_exit = arg(argc, argv, "--solver_exit", "published");  // published | latest
	int fd_in = std::atoi(arg(argc, argv, "--fd_in", "-1"));
	int fd_out = std::atoi(arg(argc, argv, "--fd_out", "-1"));
	std::string scale = arg(argc, argv, "--scale", "published");               // published | worm_1mm
	std::string fluid = arg(argc, argv, "--fluid", "quadratic_published");     // | agar_rft | viscous_rft_water
	std::string substrate = arg(argc, argv, "--substrate", "none_published");  // | agar_plate | agar_film
	std::string side_down = arg(argc, argv, "--side_down", "right");           // right | left
	double ct_arg = std::atof(arg(argc, argv, "--ct", "-1"));
	double cn_arg = std::atof(arg(argc, argv, "--cn", "-1"));
	int drag_every = std::max(1, std::atoi(arg(argc, argv, "--drag_every", "1")));

	// Environment() reads args/train_worm_swim_args.txt relative to the cwd; the caller runs us from SOFTCON_DIR.
	Environment env;
	Worm* worm = env.GetCreature();
	FEM::World* world = env.GetSoftWorld();
	if (solver_exit == "latest") world->SetReturnLatestIterate(true);
	else if (solver_exit != "published") { std::cerr << "unknown --solver_exit " << solver_exit << std::endl; return 1; }
	if (mode == "key" && !key.empty()) worm->SetKey(std::string(SOFTCON_DIR) + "/data/" + key);

	const int ratio = env.GetSimulationHz() / env.GetControlHz();
	const double dt_ctrl = 1.0 / env.GetControlHz();
	int n_ctrl = (int)std::lround(seconds * env.GetControlHz());
	const auto& muscles = worm->GetMuscles();
	const int n_act = worm->GetNumMuscleSegments();
	const int nv = world->GetPositions().size() / 3;

	std::ofstream ff(out + ".frames.f32", std::ios::binary), fa(out + ".act.f32", std::ios::binary);
	std::vector<float> buf(3 * nv), abuf(n_act);
	auto dump = [&](const Eigen::VectorXd& act) {
		const Eigen::VectorXd& x = world->GetPositions();
		for (int i = 0; i < 3 * nv; i++) buf[i] = (float)x[i];
		for (int i = 0; i < n_act; i++) abuf[i] = (float)act[i];
		ff.write((const char*)buf.data(), buf.size() * sizeof(float));
		fa.write((const char*)abuf.data(), abuf.size() * sizeof(float));
	};
	auto current_act = [&]() {
		Eigen::VectorXd a(n_act);
		int k = 0;
		for (auto m : muscles) { Eigen::VectorXd l = m->GetActivationLevels(); a.segment(k, l.size()) = l; k += l.size(); }
		return a;
	};

	// Muscle::mName has no getter; read the names in the order Worm::MakeMuscles reads them (the "o" lines).
	std::vector<std::string> names;
	{
		std::ifstream obj(std::string(SOFTCON_DIR) + "/data/worm_nerve_cord_highResCord.obj");
		for (std::string line; std::getline(obj, line);)
			if (line.rfind("o ", 0) == 0) names.push_back(line.substr(2, 3));
	}
	if (names.size() != muscles.size()) { std::cerr << "muscle name count mismatch" << std::endl; return 1; }

	Eigen::VectorXd zero_actions = Eigen::VectorXd::Zero(env.GetActionSize());
	int n_frames = 0;
	dump(Eigen::VectorXd::Zero(n_act)); n_frames++;
	const Eigen::VectorXd x_rest = world->GetPositions();
	double max_disp = 0.0;  // max over control steps of max |x - x_rest| (double precision; frames are float32)

	// Worm-scale world (header comment). Unused unless a non-published --scale/--fluid/--substrate is given.
	const bool worm_scale = scale == "worm_1mm", film = substrate == "agar_film", plate = substrate == "agar_plate" || film;
	const bool rft = fluid == "agar_rft" || fluid == "viscous_rft_water";
	if ((scale != "published" && !worm_scale) || (fluid != "quadratic_published" && !rft) ||
	    (substrate != "none_published" && !plate) || (side_down != "right" && side_down != "left")) {
		std::cerr << "unknown --scale, --fluid, --substrate or --side_down value" << std::endl; return 1; }
	if (worm_scale != rft) {
		std::cerr << "--scale worm_1mm needs an RFT --fluid (the published quadratic drag is metre scale), and an RFT "
		             "fluid needs --scale worm_1mm" << std::endl; return 1; }
	if (plate && fluid != "agar_rft") { std::cerr << "--substrate agar_plate|agar_film needs --fluid agar_rft" << std::endl; return 1; }
	const double density = 1074.0, length_m = 1e-3, g_si = 9.81;  // Reina 2013 (measured); BBC 2012 model length
	double ct = fluid == "agar_rft" ? 3.2 : 0.00357, cn = fluid == "agar_rft" ? 128.0 : 0.005675;  // Pa s
	if (ct_arg > 0) ct = ct_arg;
	if (cn_arg > 0) cn = cn_arg;
	const int n_slice = 24;
	double zmin = 1e30, zmax = -1e30, ymin = 1e30, ymax = -1e30;
	for (int i = 0; i < nv; i++) {
		zmin = std::min(zmin, x_rest[3 * i + 2]); zmax = std::max(zmax, x_rest[3 * i + 2]);
		ymin = std::min(ymin, x_rest[3 * i + 1]); ymax = std::max(ymax, x_rest[3 * i + 1]);
	}
	const double L_sim = zmax - zmin, u_m = length_m / L_sim;
	double vol = 0.0;  // closed surface, divergence theorem
	for (const auto& tr : worm->GetContours()) {
		Eigen::Vector3d p0 = x_rest.segment<3>(3 * tr[0]), p1 = x_rest.segment<3>(3 * tr[1]), p2 = x_rest.segment<3>(3 * tr[2]);
		vol += p0.dot(p1.cross(p2)) / 6.0;
	}
	vol = std::fabs(vol);
	const double mass_sim = density * vol * u_m * u_m, g_sim = g_si / u_m;
	std::vector<int> slice(nv), count(n_slice, 0);
	for (int i = 0; i < nv; i++) {
		slice[i] = std::min(n_slice - 1, (int)((x_rest[3 * i + 2] - zmin) / L_sim * n_slice));
		count[slice[i]]++;
	}
	// Which way is right: the mean y of the right muscles' (MDR, MVR) segment starts against the left ones'.
	double yr = 0, yl = 0; int nr = 0, nl = 0;
	for (size_t mi = 0; mi < muscles.size(); mi++)
		for (auto& p : muscles[mi]->GetStarts()) { if (names[mi][2] == 'R') { yr += p[1]; nr++; } else { yl += p[1]; nl++; } }
	const double right_sign = (yr / nr < yl / nl) ? -1.0 : 1.0;           // +1 if the right side is +y
	const double down = side_down == "right" ? right_sign : -right_sign;  // gravity along down * y
	const double y_plate = down < 0 ? ymin : ymax;
	const double y_film = down < 0 ? ymax : ymin;  // agar_film: the film surface at the rest thickness above the plate
	Eigen::VectorXd fext = Eigen::VectorXd::Zero(3 * nv);
	if (plate) for (int i = 0; i < nv; i++) fext[3 * i + 1] = down * (mass_sim / nv) * g_sim;
	double t_drag = 0.0; long n_drag = 0, n_phys = 0;
	auto update_drag = [&]() {
		auto c0 = std::chrono::steady_clock::now();
		const Eigen::VectorXd& x = world->GetPositions();
		std::vector<Eigen::Vector3d> c(n_slice, Eigen::Vector3d::Zero()), t(n_slice);
		for (int i = 0; i < nv; i++) c[slice[i]] += x.segment<3>(3 * i);
		for (int k = 0; k < n_slice; k++) c[k] /= count[k];
		for (int k = 0; k < n_slice; k++) t[k] = (c[std::min(k + 1, n_slice - 1)] - c[std::max(k - 1, 0)]).normalized();
		std::vector<Eigen::Triplet<double>> trip;
		trip.reserve(9 * nv);
		for (int i = 0; i < nv; i++) {
			const Eigen::Vector3d& ti = t[slice[i]];
			Eigen::Matrix3d B = (L_sim / n_slice / count[slice[i]]) *
			                    (ct * ti * ti.transpose() + cn * (Eigen::Matrix3d::Identity() - ti * ti.transpose()));
			for (int a = 0; a < 3; a++) for (int b = 0; b < 3; b++) trip.emplace_back(3 * i + a, 3 * i + b, B(a, b));
		}
		Eigen::SparseMatrix<double> C(3 * nv, 3 * nv);
		C.setFromTriplets(trip.begin(), trip.end());
		world->SetDragMatrix(C);
		t_drag += std::chrono::duration<double>(std::chrono::steady_clock::now() - c0).count();
		n_drag++;
	};
	auto project = [&]() {
		Eigen::VectorXd x = world->GetPositions(), v = world->GetVelocities();
		bool hit = false;
		for (int i = 0; i < nv; i++)
			if (down * (x[3 * i + 1] - y_plate) > 0) {
				x[3 * i + 1] = y_plate;
				if (down * v[3 * i + 1] > 0) v[3 * i + 1] = 0.0;
				hit = true;
			} else if (film && down * (x[3 * i + 1] - y_film) < 0) {
				x[3 * i + 1] = y_film;
				if (down * v[3 * i + 1] < 0) v[3 * i + 1] = 0.0;
				hit = true;
			}
		if (hit) { world->SetPositions(x); world->SetVelocities(v); }
	};
	auto step = [&]() {
		if (!rft) { env.Step(); return; }
		if (n_phys % drag_every == 0) update_drag();
		world->SetExternalForce(fext);
		world->TimeStepping();
		if (plate) project();
		n_phys++;
	};
	if (worm_scale) world->SetUnitMass(mass_sim / nv);

	auto write_json = [&](double wall) {
	std::ofstream js(out + ".json");
	js.precision(9);
	js << "{\n \"source\": \"MetaWorm (BAAIWorm b99ca5ab) sim/, driver third_party/metaworm/driver/run_body.cpp\",\n";
	js << " \"mode\": \"" << mode << "\", \"key\": \"" << key << "\", \"seconds\": " << seconds
	   << ", \"f\": " << f << ", \"lam\": " << lam << ", \"amp\": " << amp << ", \"release_at\": " << release_at
	   << ", \"solver_exit\": \"" << solver_exit << "\",\n";
	js << " \"simulation_hz\": " << env.GetSimulationHz() << ", \"control_hz\": " << env.GetControlHz()
	   << ", \"frame_dt\": " << dt_ctrl * frame_every << ", \"n_frames\": " << n_frames
	   << ", \"n_vertices\": " << nv << ", \"n_act\": " << n_act << ", \"wall_s\": " << wall << ",\n";
	js << " \"max_disp_from_rest\": " << max_disp << ",\n";
	js << " \"scale\": \"" << scale << "\", \"fluid\": \"" << fluid << "\", \"substrate\": \"" << substrate
	   << "\", \"side_down\": \"" << side_down << "\",\n";
	if (worm_scale)
		js << " \"world\": {\"length_unit_m\": " << u_m << ", \"rest_length_units\": " << L_sim << ", \"volume_units\": "
		   << vol << ", \"density_kg_m3\": " << density << ", \"mass_units\": " << mass_sim << ", \"mass_kg\": "
		   << mass_sim * u_m << ", \"ct_Pa_s\": " << ct << ", \"cn_Pa_s\": " << cn << ", \"drag_every\": " << drag_every
		   << ", \"n_drag_updates\": " << n_drag << ", \"drag_update_s_mean\": " << (n_drag ? t_drag / n_drag : 0.0)
		   << ", \"gravity_units_s2\": " << (plate ? g_sim : 0.0) << ", \"plate_axis\": 1, \"plate_down\": " << down
		   << ", \"plate_y\": " << y_plate << ", \"film_y\": " << (film ? y_film : 0.0) << "},\n";
	js << " \"muscles\": [";
	for (size_t i = 0; i < names.size(); i++) js << (i ? ", " : "") << "\"" << names[i] << "\"";
	js << "],\n \"segment_starts\": [";
	bool first = true;
	for (auto m : muscles) for (auto& p : m->GetStarts()) { js << (first ? "" : ", ") << "[" << p[0] << ", " << p[1] << ", " << p[2] << "]"; first = false; }
	js << "],\n \"segment_ends\": [";
	first = true;
	for (auto m : muscles) for (auto& p : m->GetEnds()) { js << (first ? "" : ", ") << "[" << p[0] << ", " << p[1] << ", " << p[2] << "]"; first = false; }
	js << "],\n \"triangles\": [";
	const auto& tri = worm->GetContours();
	for (size_t i = 0; i < tri.size(); i++) js << (i ? ", " : "") << "[" << tri[i][0] << ", " << tri[i][1] << ", " << tri[i][2] << "]";
	js << "]\n}\n";
	};

	auto t0 = std::chrono::steady_clock::now();
	if (mode == "pipe") {
		auto rd = [&](void* p, size_t n) { char* c = (char*)p; while (n) { ssize_t k = read(fd_in, c, n); if (k <= 0) return false; c += k; n -= k; } return true; };
		auto wr = [&](const void* p, size_t n) { const char* c = (const char*)p; while (n) { ssize_t k = write(fd_out, c, n); if (k <= 0) return false; c += k; n -= k; } return true; };
		if (fd_in < 0 || fd_out < 0) { std::cerr << "pipe mode needs --fd_in and --fd_out" << std::endl; return 1; }
		write_json(0.0);
		int32_t hdr[2] = {nv, n_act};
		double dt_phys = 1.0 / env.GetSimulationHz();
		wr(hdr, sizeof(hdr)); wr(&dt_phys, sizeof(double)); wr(x_rest.data(), 3 * nv * sizeof(double));
		Eigen::VectorXd a(n_act);
		for (;;) {
			int32_t msg[2];
			if (!rd(msg, sizeof(msg)) || msg[0] <= 0) break;
			if (!rd(a.data(), n_act * sizeof(double))) break;
			worm->SetActivationLevelsDirectly(a);
			for (int i = 0; i < msg[0]; i++) step();
			const Eigen::VectorXd& x = world->GetPositions();
			max_disp = std::max(max_disp, (x - x_rest).cwiseAbs().maxCoeff());
			if (msg[1] & 1) { dump(current_act()); n_frames++; }
			if (!wr(x.data(), 3 * nv * sizeof(double))) break;
		}
		n_ctrl = 0;
	}
	for (int c = 0; c < n_ctrl; c++) {
		double t = c * dt_ctrl;
		if (t >= release_at - 1e-12) {
			worm->SetActivationLevelsDirectly(Eigen::VectorXd::Zero(n_act));
		} else if (mode == "key") {
			env.SetActions(zero_actions);
		} else {
			Eigen::VectorXd a = Eigen::VectorXd::Zero(n_act);
			if (mode == "wave") {
				double ramp = std::min(1.0, t * f);
				int k = 0;
				for (size_t mi = 0; mi < muscles.size(); mi++) {
					bool dorsal = names[mi].rfind("MD", 0) == 0;  // MDR, MVR, MDL, MVL
					int ns = muscles[mi]->GetNumSampling();
					for (int j = 0; j < ns; j++) {
						double s = (j + 0.5) / ns;
						double ph = 2 * M_PI * (f * t - s / lam);
						a[k + j] = ramp * amp * 0.5 * (1.0 + (dorsal ? 1.0 : -1.0) * std::sin(ph));
					}
					k += ns;
				}
			}
			worm->SetActivationLevelsDirectly(a);
		}
		for (int i = 0; i < ratio; i++) step();
		max_disp = std::max(max_disp, (world->GetPositions() - x_rest).cwiseAbs().maxCoeff());
		if ((c + 1) % frame_every == 0) { dump(current_act()); n_frames++; }
	}
	double wall = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
	ff.close(); fa.close();

	write_json(wall);
	std::cout << "done " << n_frames << " frames, wall " << wall << " s" << std::endl;
	return 0;
}
