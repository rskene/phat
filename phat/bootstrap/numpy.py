import warnings
import numpy as np

def A_dani(n1, k1):
    return (np.log(k1)/(2*np.log(n1) - np.log(k1)))**(2*(np.log(n1) - np.log(k1))/(np.log(n1)))

def A_qi(n1, k1):
    return (1 - (2*(np.log(k1) - np.log(n1))/(np.log(k1))))**(np.log(k1)/np.log(n1) - 1)

def moments_dbs_prefactor(xi_n, n1, k1):
    """ 
    Function to calculate pre-factor used in moments
    double-bootstrap procedure.
    Args:
        xi_n: moments tail index estimate corresponding to
              sqrt(n)-th order statistic.
        n1:   size of the 1st bootstrap in double-bootstrap
              procedure.
        k1:   estimated optimal order statistic based on the 1st
              bootstrap sample.
    Returns:
        prefactor: constant used in estimation of the optimal
                   stopping order statistic for moments estimator.
    """
    def V_sq(xi_n):
        if xi_n >= 0:
            V = 1. + (xi_n)**2
            return V
        else:
            a = (1.-xi_n)**2
            b = (1-2*xi_n)*(6*((xi_n)**2)-xi_n+1)
            c = (1.-3*xi_n)*(1-4*xi_n)
            V = a*b/c
            return V

    def V_bar_sq(xi_n):
        if xi_n >= 0:
            V = 0.25*(1+(xi_n)**2)
            return V
        else:
            a = 0.25*((1-xi_n)**2)
            b = 1-8*xi_n+48*(xi_n**2)-154*(xi_n**3)
            c = 263*(xi_n**4)-222*(xi_n**5)+72*(xi_n**6)
            d = (1.-2*xi_n)*(1-3*xi_n)*(1-4*xi_n)
            e = (1.-5*xi_n)*(1-6*xi_n)
            V = a*(b+c)/(d*e)
            return V
    
    def b(xi_n, rho):
        if xi_n < rho:
            a1 = (1.-xi_n)*(1-2*xi_n)
            a2 = (1.-rho-xi_n)*(1.-rho-2*xi_n)
            return a1/a2
        elif xi_n >= rho and xi_n < 0:
            return 1./(1-xi_n)
        else:
            b = (xi_n/(rho*(1.-rho))) + (1./((1-rho)**2))
            return b

    def b_bar(xi_n, rho):
        if xi_n < rho:
            a1 = 0.5*(-rho*(1-xi_n)**2)
            a2 = (1.-xi_n-rho)*(1-2*xi_n-rho)*(1-3*xi_n-rho)
            return a1/a2
        elif xi_n >= rho and xi_n < 0:
            a1 = 1-2*xi_n-np.sqrt((1-xi_n)*(1-2.*xi_n))
            a2 = (1.-xi_n)*(1-2*xi_n)
            return a1/a2
        else:
            b = (-1.)*((rho + xi_n*(1-rho))/(2*(1-rho)**3))
            return b

    rho = np.log(k1)/(2*np.log(k1) - 2.*np.log(n1))
    a = (V_sq(xi_n)) * (b_bar(xi_n, rho)**2)
    b = V_bar_sq(xi_n) * (b(xi_n, rho)**2)
    prefactor = (a/b)**(1./(1. - 2*rho))
    return prefactor

def hill_est_for_alpha(k, y):
    return k / (np.cumsum(np.log(y[:-1])) - k*np.log(y[:-1]))

def hill_est_for_xi(k,y):
    return np.cumsum(np.log(y[:-1]))/k - np.log(y[1:])

def second_moment(k, y):
    t1 = np.cumsum(np.log(y[:-1])**2) / k 
    t2 = 2*np.cumsum(np.log(y[:-1]))*np.log(y[1:]) / k
    t3 = np.log(y[1:])**2
    return t1 - t2 + t3

def third_moment(k,y):
    """
    """
    t1 = (1/k)*np.cumsum(np.log(y[:-1])**3)
    t2 = (3*np.log(y[1:])/k)*np.cumsum(np.log(y[:-1])**2)
    t3 = (3*np.log(y[1:])**2/k)*np.cumsum(np.log(y[:-1]))
    t4 = np.log(y[1:])**3
    M3 = t1 - t2 + t3 - t4
    return M3

def amse(M1, M2):
    return (M2 - 2*M1**2)**2

def hill_amse(k,y):
    M1 = hill_est_for_xi(k,y)
    M2 = second_moment(k,y)
    return amse(M1,M2)    

def moments_amse(k, y):
    M1 = hill_est_for_xi(k, y)
    M2 = second_moment(k,y)    
    M3 = third_moment(k, y)
    xi_2 = M1 + 1 - 0.5*((1 - (M1*M1)/M2))**(-1)
    xi_3 = np.sqrt(0.5*M2) + 1 - (2/3)*(1 / (1 - M1*M2/M3))
    return (xi_2 - xi_3)**2

def k_finder(y, n, r, kmin, style='hill'):
    kmax = (np.abs(np.linspace(1./n, 1.0, n) - 1)).argmin()
    amses = np.zeros((r, n-1))
    for i in range(r):
        sample = np.random.choice(y, n, replace=False)
        sample = np.sort(sample)[::-1]
        k = np.arange(1,n)

        if style == 'hill':
            amses[i] = hill_amse(k,sample)
        elif style =='moments':
            amses[i] = moments_amse(k,sample)
        else:
            raise ValueError('`style` not supported')

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        amse_for_k = np.nanmean(amses, axis=0)
    k = np.nanargmin(amse_for_k[kmin:kmax]) + 1 + kmin
    return k

def dbl_bs(y, t=.5, r=500, style='hill', A_type='qi'):
    n = y.size
    n1 = int(np.sqrt(t)*n)
    n2 = int(t*n)
    k = np.arange(1, y.size)
    xi = hill_est_for_xi(k,y)
    xi_n = xi[int(np.floor(n**0.5))-1]

    kmin1, kmin2 = 1,1
    while True:
        k1 = k_finder(y, n1, r, kmin1, style=style)
        k2 = k_finder(y, n2, r, kmin2, style=style)

        if k2 > k1:
            kmin1 += int(0.005*n)
            kmin2 += int(0.005*n)
        else:
            break

    A = A_qi if A_type == 'qi' else A_dani

    if style == 'hill':
        prefactor = A(n1,k1)
    elif style =='moments':
        prefactor = moments_dbs_prefactor(xi_n, n1, k1)
    else:
        raise ValueError('`style` not supported')

    k_star = prefactor*k1**2 / k2
    k_star = np.round(k_star).astype(int)

    if k_star >= n:
        raise ValueError(f'Estimated threshold larger than size of sample data: k {k_star} v. n {n}')
    else:
        k_star = 2 if k_star == 0 else k_star

    return xi[k_star]