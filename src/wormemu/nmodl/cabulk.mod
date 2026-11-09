TITLE Bulk cytosolic Ca of a neuron soma, a readout pool: radial diffusion, fixed-ratio buffer, membrane pump

COMMENT
Port of NEURON's cadifpmp (Hines and Carnevale; NEURON 9.0.2 share/nrn/demo/release/cabpump.mod).
The NEURON distribution's notice, retained as its licence requires:

Copyright (c) 2018, Michael Hines
All rights reserved.

This Copyright refers to all files in this distribution that do not have
an explicit Copyright notice. See:
grep -r '\<Copyright\>' *

All files are intended to have a license compatible with the following
"three clause" open source BSD license.  Please notify
michael.hines@yale.edu if you believe any file is not compatible with
the "three clause" open source BSD license. 

Redistribution and use in source and binary forms, with or without
modification are permitted provided that the following conditions are met:

1.  Redistributions of source code must retain the above copyright
notice, this list of conditions, and the following disclaimer.

2.  Redistributions in binary form must reproduce the above copyright
notice, this list of conditions, and the following disclaimer in the
documentation and/or other materials provided with the distribution. 

3.  Neither the name of the copyright holder nor the names of its
contributors may be used to endorse or promote products derived from
this software without specific prior written permission. 

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Wormemu changes (wbrain2, 8 Nov 2026; mech/capool's ca_bulk toggle), each to keep the pool a readout beside
Nicoletti 2019's Eq. 28 pool (cainternm), which every Ca-dependent channel keeps reading:
  - SUFFIX cabulk; USEION ca READ ica with no WRITE: cai stays cainternm's, and the pump's current is not added to
    the membrane (cadifpmp writes it to ica). The influx is the soma's whole ica; cadifpmp's influx is ica minus the
    pump's own last current, the same thing when the pump writes none.
  - external Ca is the GLOBAL caom (mM), set by mech/capool from the ledger's ion_cao, instead of the ion's cao: the
    brain holds the Ca ion in uM (cao0 = ion_cao x 1000), cadifpmp's rates are per mM.
  - the state is ca[] in mM as cadifpmp; ca0 (uM, RANGE) is the initial free Ca in every annulus (cadifpmp starts
    from cai, which BAAIWorm's cainternm holds in uM), and the pump starts in equilibrium with it as cadifpmp's
    INITIAL computes it (cadifpmp's renormalisation, skipped when the total pump is below 1e-9 mol/cm2, so always
    at pump0 3e-14, is kept as written).
  - cab (uM, RANGE): the annuli's volume-weighted mean free Ca, the indicator's input; cabmem (uM): ca[0].
Everything else (annulus coordinates, the KINETIC scheme, the rate constants and their area scaling) is cadifpmp's.
ENDCOMMENT

NEURON {
	SUFFIX cabulk
	USEION ca READ ica
	RANGE ca0, cab, cabmem, jpump
	GLOBAL vol, pump0, DFree, beta, k1, k2, k3, k4, caom
}

DEFINE NANN  10

UNITS {
	(mV)	= (millivolt)
	(molar) = (1/liter)
	(mM)	= (millimolar)
	(uM)	= (micromolar)
	(um)	= (micron)
	(mA)	= (milliamp)
	(mol)	= (1)
	FARADAY = (faraday)	 (coulomb)
	PI	= (pi)		(1)
}

PARAMETER {
	DFree = .6	(um2/ms) <0,1e9>
	beta = 50		<0, 1e9>
	k1 = 5e8        (/mM-s) <0, 1e10>
	k2 = .25e6      (/s)	<0, 1e10>
	k3 = .5e3       (/s)	<0, 1e10>
	k4 = 5e0        (/mM-s)	<0, 1e10>
	pump0 = 3e-14 (mol/cm2) <0, 1e9>
	ca0 = 0.05 (uM)
	caom = 2 (mM)
}

ASSIGNED {
	diam		(um)
	ica		(mA/cm2)
	vol[NANN]	(1)
	area1    (um2)
	c1      (1+8 um5/ms)
	c2      (1-10 um2/ms)
	c3      (1-10 um2/ms)
	c4      (1+8 um5/ms)
	cab	(uM)
	cabmem	(uM)
	jpump	(mA/cm2)
}

STATE {
	ca[NANN]	(mM) <1e-6>
	pump    (mol/cm2)	<1e-15>
	pumpca  (mol/cm2)	<1e-15>
}

INITIAL {LOCAL total
	parms()
	FROM i=0 TO NANN-1 {
		ca[i] = ca0/1000
	}
	pumpca = ca[0]*pump*c1/c2
	total = pumpca + pump
	if (total > 1e-9) {
		pump = pump*(pump/total)
		pumpca = pumpca*(pump/total)
	}
	jpump = 0
	mean()
}

BREAKPOINT {
	SOLVE state METHOD sparse
	mean()
}

LOCAL frat[NANN]

PROCEDURE coord() {
	LOCAL r, dr2
	r = 1/2
	dr2 = r/(NANN-1)/2
	vol[0] = 0
	frat[0] = 2*r
	FROM i=0 TO NANN-2 {
		vol[i] = vol[i] + PI*(r-dr2/2)*2*dr2
		r = r - dr2
		frat[i+1] = 2*PI*r/(2*dr2)
		r = r - dr2
		vol[i+1] = PI*(r+dr2/2)*2*dr2
	}
}

KINETIC state {
	COMPARTMENT i, (1+beta)*diam*diam*vol[i]*1(um) {ca}
	COMPARTMENT (1e10)*area1 {pump pumpca}
	~ pumpca <-> pump + caom		(c3, c4)
	jpump = (1e-4)*2*FARADAY*(f_flux - b_flux)/area1
	~ ca[0] << (-ica*PI*diam*1(um)*(1e4)*frat[0]/(2*FARADAY))
	FROM i=0 TO NANN-2 {
		~ ca[i] <-> ca[i+1] (DFree*frat[i+1]*1(um), DFree*frat[i+1]*1(um))
	}
	~ ca[0] + pump <-> pumpca	(c1, c2)
}

PROCEDURE mean() {LOCAL s, w
	s = 0
	w = 0
	FROM i=0 TO NANN-1 {
		s = s + ca[i]*vol[i]
		w = w + vol[i]
	}
	cab = 1000*s/w
	cabmem = 1000*ca[0]
}

PROCEDURE parms() {
	coord()
	area1 = 2*PI*(diam/2) * 1(um)
	c1 = (1e7)*area1 * k1
	c2 = (1e7)*area1 * k2
	c3 = (1e7)*area1 * k3
	c4 = (1e7)*area1 * k4
}
