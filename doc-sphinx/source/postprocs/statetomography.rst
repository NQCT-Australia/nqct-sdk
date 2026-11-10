.. _statetomography:

State Tomography
================

To get the full description of a given quantum state, one performs multiple basis measurements to obtain the density-matrix. There are in-built utilities to perform state tomography as shown in the :doc:`worked example <../examples/Tomography>`. This article explains the steps performed in said tomography package.

Basics
------

Recall that a density matrix :math:`\rho` must satisfy:

- Hermiticity: :math:`\rho^\dagger=\rho`
- Unit-Trace: :math:`\textnormal{tr}(\rho)=1`
- Positive semi-definiteness: :math:`\rho` has non-negative eigenvalues

The Hermicitity readily implies the orthogonal (under the inner-product :math:`\langle A|B\rangle=\textnormal{tr}(AB)`) Pauli decomposition:

.. math::
    \rho=\left(\begin{matrix}I+z & x-iy\\x+iy & I-z\end{matrix}\right)\equiv\frac{1}{2}(I_2+r_x\sigma_x+r_y\sigma_y+r_z\sigma_z)

where :math:`(r_x,r_y,r_z)` is the Bloch-vector with the magnitude being unity for pure-states. It is evident that :math:`\langle r_m\rangle\equiv\textnormal{tr}(\rho\sigma_m)=r_m`. Thus, one can find the Bloch-vector by measuring along the :math:`x`, :math:`y` and :math:`z` axes on the Bloch sphere. This can be achieved by rotating the state's basis components onto the measurement :math:`z`-axis:

- :math:`\langle z\rangle`: just measure
- :math:`\langle x\rangle`: perform a y-rotation :math:`Y(-\pi/2)` to rotate :math:`x` axis onto the :math:`z` axis and then measure
- :math:`\langle y\rangle`: perform a x-rotation :math:`X(\pi/2)` to rotate :math:`y` axis onto the :math:`z` axis and then measure

This procedure of preparing the state three times to perform different basis measurements can help reconstruct the density matrix for a single qubit. To extend the procedure to multiple qubits, realise that an :math:`N`-qubit density matrix is simply the tensor product :math:`\rho_1\otimes\rho_2\otimes...\otimes\rho_N`. Taking the decomposition from before, this leads to a linear combination of all Pauli matrices:

.. math::
    \rho=\frac{1}{2^N}\sum_{i_1,...,i_N}^NC_{i_1,...,i_N}\sigma_{i_1}\otimes...\otimes\sigma_{i_N},\hspace{1cm}\sigma_{i}\in\{I_2,\sigma_x,\sigma_y,\sigma_z\}.

The coefficients :math:`C_{i_1,...,i_N}` can be found by performing simultaneous qubit measurements on the :math:`i_1,...,i_N` axes. Note that they are by definition joint parity measurements. For example, :math:`\langle\sigma_z\otimes\sigma_z\rangle` gives the product of the individual :math:`z`-measurements. So if one measures 01 then the first qubit gives +1 while the second qubit gives -1 to both give +1x-1=-1. The measurement bases are done in the same way as the single-qubit case. For example, with 4 qubits, :math:`C_{1423}` corresponds to doing nothing on the first qubit (i.e. :math:`I_2` requires no measurement), a normal :math:`z` measurement on the second qubit, an :math:`x` measurement on the third qubit (i.e. via the :math:`y` rotation as discussed above) and a :math:`y` measurement on the fourth qubit (i.e. via the :math:`x` rotation as discussed above).

Thus, the measurement protocol amounts to preparing the state, applying any appropriate basis rotations and measuring all qubits over the :math:`4^N` possible states.


Actual Reconstruction
---------------------

In the experiment one prepares the same state over :math:`4^N` sequences to get the coefficients :math:`C_{i_1,...,i_N}`. Note that for each sequence, one needs to take a set of measurement :math:`M` shots (e.g. 1024) to get :math:`N` streams of :math:`M` numbers (each being either 0 or 1). One could just map :math:`\{0,1\}\to\{1,-1\}` and take the product across each measurement shot and then take the average across all :math:`M` shots. However, if performing readout correction, there needs to be a vector of populations. This is calculated via:

- Treat each :math:`N`-vector as a binary number and increment said index in a :math:`2^N`-array. For example, for 4 qubits, if the measurement was 1010, then increment index 10.
- Divide the :math:`2^N`-array by :math:`M` to get the mean population probabilities. Apply readout correction to shift the probabilities. This vector is the population vector along the :math:`N`-qubit computatational basis.
- Now to calculate the expectation :math:`\langle\sigma_{i_1}\otimes...\otimes\sigma_{i_N}\rangle`, one sums over the probability-weighted sum of all basis vector parities.

To understand the last step, just take the example for two qubits with the probability vector being (0.1,0.4,0.4,0.1) over the basis 00, 01, 10 and 11:

- 00 contributes +1, 01 contributes -1, 10 contributes -1 and 11 contributes 11
- Thus, the expectation is: 0.1-0.4-0.4+0.1 = -0.6

That is, it is a parity measurement where for each computational basis vector, just count the number of 1s; if it is odd, then it's -1 and +1. Then multiply by the probability and sum over all computational basis vectors.

Upon finding :math:`C_{i_1,...,i_N}`, one could naively sum it with the appropriate Pauli-matrix tensor products. However, the resulting matrix will likely be an invalid density matrix for it will violate unit-trace and positive semi-definiteness. Thus, the utility class :class:`sqdtoolz.Utilities.DataDensityMatrix.DataDensityMatrix` employs an optimisation procedure where one first realises that a matrix :math:`A` is positive semi-definite if and only if :math:`A=T^\dagger T`:

1. Initialise matrix :math:`T\in\mathbb{C}^{2^N}\times\mathbb{C}^{2^N}`
2. Take the candidate :math:`T` and calculate :math:`\rho'=T^\dagger T/\textnormal{tr}(T^\dagger T)`
3. Calculate all :math:`4^N` values of :math:`C'_{i_1,...,i_N}=\textnormal{tr}(\rho'(\sigma_{i_1}\otimes...\otimes\sigma_{i_N}))`.
4. Calculate :math:`\mathcal{L}=\sum_{i_1,...,i_N}^N(C'_{i_1,...,i_N}-C_{i_1,...,i_N})^2`
5. Minimise :math:`\mathcal{L}` over the :math:`2^N\times2^N\times2` real-valued numbers in :math:`T` (going back to step 2 to recalculate the new :math:`\mathcal{L}`)

The minimiser just uses ``BFGS`` via ``scipy.optimize.minimize``. By construction the final :math:`\rho=T^\dagger T` yields a valid density matrix.
