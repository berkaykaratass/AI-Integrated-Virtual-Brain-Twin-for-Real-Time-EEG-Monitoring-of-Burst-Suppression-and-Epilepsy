import numpy as np
from scipy.signal import hilbert, butter, filtfilt

def butter_bandpass(lowcut, highcut, fs, order=4):
    """Generates Butterworth bandpass filter coefficients."""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter(data, lowcut, highcut, fs, order=4):
    """
    Apply a bandpass filter to the data.
    
    Args:
        data (np.ndarray): 1D or 2D array of signal data.
        lowcut (float): Lower frequency bound (Hz).
        highcut (float): Upper frequency bound (Hz).
        fs (float): Sampling rate (Hz).
        order (int): Filter order.
    """
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def extract_analytic_signal(data):
    """
    Computes the analytic signal using Hilbert Transform.
    Returns: analytics_signal (complex)
    """
    return hilbert(data)

def extract_instantaneous_phase(data):
    """
    Extracts instantaneous phase from signal.
    Returns values in [-pi, pi].
    """
    analytic_signal = extract_analytic_signal(data)
    return np.angle(analytic_signal)

def extract_amplitude_envelope(data):
    """
    Extracts amplitude envelope (magnitude of analytic signal).
    """
    analytic_signal = extract_analytic_signal(data)
    return np.abs(analytic_signal)
