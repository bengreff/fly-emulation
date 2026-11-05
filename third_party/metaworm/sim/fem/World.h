#ifndef __WORLD__H__
#define __WORLD__H__
#include <Eigen/Core>
#include <Eigen/SparseCore>
#include <Eigen/SparseCholesky>
#include "Constraint/ConstraintHeader.h"
#include <vector>
namespace FEM
{	
class Constraint;
class World
{
public:
	World(
		double time_step = 1.0/100.0,
		int max_iteration = 100,
		double damping_coeff = 0.999,
		bool is_precessing_collision = false
		);
	void 								Initialize();
	void								Reset();

	void								AddBody(const Eigen::VectorXd& x0, const std::vector<Constraint*>& c, const double& mass = 1.0);
	void								AddConstraint(Constraint* c);
	void								RemoveConstraint(Constraint* c);

	void 								TimeStepping(bool isIntegrated = true);
	void 								UpdatePositionsAndVelocities(const Eigen::VectorXd& x_n1);

	Eigen::VectorXd						ProjectiveDynamicsMethod();
	void 								PreComputation();
	void								EvaluateJMatrix(Eigen::SparseMatrix<double>& J);
	void								EvaluateLMatrix(Eigen::SparseMatrix<double>& L);
	void								EvaluateDVector(const Eigen::VectorXd& x,Eigen::VectorXd& d);
	void								FactorizeLDLT(const Eigen::SparseMatrix<double>& A,Eigen::SimplicialLDLT<Eigen::SparseMatrix<double>>& ldltSolver);

	void								SetExternalForce(Eigen::VectorXd external_force);
	const Eigen::VectorXd&				GetExternalForce() {return mExternalForces;};

	const double&						GetTimeStep(){ return mTimeStep; };
	const double&						GetTime(){ return mTime; };

	const std::vector<Constraint*>&		GetConstraints(){return mConstraints;};
	const Eigen::VectorXd& 				GetPositions(){return mX;};
	const Eigen::VectorXd& 				GetVelocities(){return mV;};
	const int&		 					GetNumVertices(){return mNumVertices;};

	void 								SetPositions(Eigen::VectorXd& newX) { mX = newX; };
	void 								SetVelocities(Eigen::VectorXd& newV) { mV = newV; };

	// wormemu extension (2026-11-05, not upstream; inert unless called, see third_party/metaworm/UPSTREAM.md):
	// SetUnitMass replaces the per-vertex mass; SetDragMatrix adds a linear drag force -C v_{n+1} (C symmetric,
	// 3n x 3n) solved implicitly with the step, so stiff viscous or agar drag stays stable at any mass.
	void								SetUnitMass(double unit_mass);
	void								SetDragMatrix(const Eigen::SparseMatrix<double>& C);
	// SetReturnLatestIterate(true): on convergence return the latest solve, not the one before it (see World.cpp).
	void								SetReturnLatestIterate(bool on);

private:
	bool								mReturnLatest = false;
	bool								mHasDrag = false;
	bool								mDragPatternDone = false;
	Eigen::SparseMatrix<double>			mDragMatrix;
	bool 								mIsInitialized;
	bool								mIsCollision;

	std::vector<Constraint*>			mConstraints;
	int 								mConstraintDofs;
	int 								mNumVertices;

	double 								mTimeStep;
	double 								mTime;
	int 								mFrame;
	int 								mMaxIteration;
	double 								mDampingCoefficient;

	Eigen::VectorXd						mX,mV;
	Eigen::VectorXd						mInitX,mInitV;
	Eigen::VectorXd						mExternalForces;
	Eigen::VectorXd						mQn;

	std::vector<double>			 		mUnitMass;
	Eigen::SparseMatrix<double> 		mMassMatrix;
	Eigen::SparseMatrix<double> 		mInvMassMatrix;
	Eigen::SparseMatrix<double> 		mIdentityMatrix;

	Eigen::SparseMatrix<double> 		mJ,mL;
	Eigen::SimplicialLDLT<Eigen::SparseMatrix<double>>	mDynamicSolver,mQuasiStaticSolver;
};
};
#endif