from smurfs.analyze.timerseries import *


def find_frequencies(data : np.ndarray, snr_cutoff : float, window_size : float) -> List[Tuple[float, float, float, float, float]]:
    print(term.format(f"Nyquist frequency: {nyquistFrequency(data)} c/d", term.Color.CYAN))
    lc_res = data

    snr = None
    n = 1
    resulting_frequencies  = []

    while snr == None or snr > snr_cutoff:
        fit,lc_res,snr,residual_noise = reduce_max_f(lc_res,window_size)
        print(term.format(
            "F" + str(n) + "  " + str(fit[1]) + "c/d     " + str(fit[0]) + "     " + str(fit[2]) + "    " + str(
                snr),term.Color.CYAN))
        resulting_frequencies.append((fit[1],snr,fit[0],fit[2],residual_noise))
        n+=1
    return resulting_frequencies

def reduce_max_f(lc_res : np.ndarray,window_size : float) -> Tuple[List[float],np.ndarray,float,float]:
    amp = amplitude_spectrum(lc_res)
    snr = signal_to_noise_max_f(amp, window_size)
    fit, lc_res = remove_max_frequency(lc_res, amp)
    residual_noise = float(np.mean(lc_res))

    return fit,lc_res,snr,residual_noise
