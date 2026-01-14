# Hapag Farm - Binary Logic Crop Recommendation System

def get_npk_binary_code(n, p, k):
    """
    Convert NPK values to 5-bit binary code
    Bit positions: [N_high, N_low, P_high, P_low, K_high]
    """
    # Thresholds in ppm
    N_LOW = 88.9
    N_HIGH = 177.8
    P_LOW = 4.1
    P_HIGH = 8.1
    K_LOW = 40.7
    K_HIGH = 103.7
    
    # Determine N bits
    n_high = 1 if n > N_HIGH else 0
    n_low = 1 if n < N_LOW else 0
    
    # Determine P bits
    p_high = 1 if p > P_HIGH else 0
    p_low = 1 if p < P_LOW else 0
    
    # Determine K bit
    k_high = 1 if k > K_HIGH else 0
    
    # Create 5-bit binary code
    binary_code = f"{n_high}{n_low}{p_high}{p_low}{k_high}"
    return binary_code

def get_crops_from_binary(binary_code):
    """
    Map binary code to recommended crops
    """
    crop_map = {
        "00000": [],
        "00001": ["OKRA", "GARLIC"],
        "00010": ["ONION"],
        "00011": ["SWEET POTATOES", "SITAW"],
        "00100": [],
        "00101": [],
        "00110": ["BANANA", "ONION"],
        "00111": ["LETTUCE", "RADISH", "SITAW"],
        "01000": [],
        "01001": ["LETTUCE", "GARLIC"],
        "01010": ["ONION"],
        "01011": ["SITAW"],
        "01100": [],
        "01101": [],
        "01110": [],
        "01111": ["LETTUCE", "CHILI", "BELL PEPPERS", "BROCCOLI", "CORN", "TOMATOES", "EGGPLANT"],
        "10000": ["CABBAGE", "CORN", "MUSTASA"],
        "10001": ["LETTUCE", "GARLIC"],
        "10010": ["LETTUCE", "CABBAGE", "MUSTASA"],
        "10011": ["TOMATOES", "CHILI", "BELL PEPPERS", "BROCCOLI", "CORN"],
        "10100": ["TOMATOES", "CABBAGE", "KANGKONG", "MUSTASA"],
        "10101": ["CHILI", "BELL PEPPERS"],
        "10110": ["BANANA", "ONION", "KANGKONG", "MUSTASA"],
        "10111": ["EGGPLANT", "CORN", "TOMATOES"],
        "11000": ["CABBAGE", "CORN", "MUSTASA"],
        "11001": ["EGGPLANT", "LETTUCE"],
        "11010": ["CABBAGE", "ONION", "MUSTASA"],
        "11011": ["TOMATOES", "EGGPLANT", "CABBAGE", "BROCCOLI", "CORN", "CHILI", "BELL PEPPERS"],
        "11100": ["TOMATOES", "CABBAGE", "KANGKONG", "MUSTASA"],
        "11101": ["CABBAGE"],
        "11110": ["CABBAGE", "ONION", "KANGKONG", "MUSTASA"],
        "11111": ["TOMATOES", "EGGPLANT", "CABBAGE", "BROCCOLI", "CORN", "CHILI", "BELL PEPPERS", "LETTUCE"]
    }
    
    return crop_map.get(binary_code, [])

def get_binary_crop_recommendation(n, p, k):
    """
    Get crop recommendation using binary logic system
    Returns: (crops_list, binary_code, confidence)
    """
    binary_code = get_npk_binary_code(n, p, k)
    crops = get_crops_from_binary(binary_code)
    
    # Calculate confidence based on how many crops match
    confidence = 95 if len(crops) > 0 else 0
    
    return crops, binary_code, confidence

def get_npk_status(n, p, k):
    """
    Get human-readable NPK status
    """
    N_LOW = 88.9
    N_HIGH = 177.8
    P_LOW = 4.1
    P_HIGH = 8.1
    K_LOW = 40.7
    K_HIGH = 103.7
    
    n_status = "HIGH" if n > N_HIGH else ("LOW" if n < N_LOW else "MEDIUM")
    p_status = "HIGH" if p > P_HIGH else ("LOW" if p < P_LOW else "MEDIUM")
    k_status = "HIGH" if k > K_HIGH else ("LOW" if k < K_LOW else "MEDIUM")
    
    return {
        "N": n_status,
        "P": p_status,
        "K": k_status
    }
