"""
Sensor fusion logic for combining multiple sensor readings.
"""
import math
import time
import statistics
from typing import List, Tuple, Dict, Optional


class SensorFusion:
    """Combines multiple sensor readings with reliability weighting."""
    
    # Sensor-type specific half-life (seconds)
    # Optimized for office environment real-time responsiveness
    HALF_LIFE = {
        "temperature": 120,    # 2 minutes (gradual changes)
        "humidity": 120,       # 2 minutes
        "co2": 60,            # 1 minute (rapid changes with occupancy)
        "illuminance": 120,    # 2 minutes
        "occupancy": 30,       # 30 seconds (real-time critical)
        "pir": 10,            # 10 seconds (motion detection)
        "default": 120         # 2 minutes default
    }
    
    def __init__(self):
        # Sensor reliability scores (0.0 - 1.0)
        # These can be configured or learned over time
        self.sensor_reliability: Dict[str, float] = {
            "default": 0.5,
        }
        
        # Adaptive mode (future enhancement)
        self.adaptive_mode = False
        self.variance_history: Dict[str, List[float]] = {}
    
    def set_reliability(self, sensor_id: str, score: float):
        """Set reliability score for a specific sensor."""
        if not 0.0 <= score <= 1.0:
            raise ValueError("Reliability score must be between 0.0 and 1.0")
        self.sensor_reliability[sensor_id] = score
    
    def _get_half_life(self, sensor_type: str, readings: List[Tuple[str, float, float]]) -> float:
        """
        Get half-life for sensor type, with optional adaptive adjustment.
        
        Args:
            sensor_type: Type of sensor (temperature, co2, occupancy, etc.)
            readings: Recent readings for adaptive calculation
            
        Returns:
            Half-life in seconds
        """
        base_half_life = self.HALF_LIFE.get(sensor_type, self.HALF_LIFE["default"])
        
        # Future enhancement: Adaptive half-life based on data variance
        if self.adaptive_mode and len(readings) >= 5:
            
            values = [v for _, v, _ in readings]
            variance = statistics.variance(values) if len(values) > 1 else 0
            
            # Store variance history for learning
            if sensor_type not in self.variance_history:
                self.variance_history[sensor_type] = []
            self.variance_history[sensor_type].append(variance)
            
            # Keep last 100 variance samples
            if len(self.variance_history[sensor_type]) > 100:
                self.variance_history[sensor_type].pop(0)
            
            # Adaptive adjustment (placeholder - needs tuning with real data)
            # High variance → shorter half-life (more responsive)
            # Low variance → longer half-life (more stable)
            if variance > 1.0:  # High variance threshold
                return base_half_life * 0.5  # Reduce by 50%
            elif variance < 0.1:  # Low variance threshold
                return base_half_life * 1.5  # Increase by 50%
        
        return base_half_life
    
    def fuse_temperature(
        self, 
        readings: List[Tuple[str, float, float]], 
        sensor_type: str = "temperature"
    ) -> Optional[float]:
        """
        Fuse multiple temperature readings with weighted average.
        
        Args:
            readings: List of (sensor_id, value, timestamp) tuples
            sensor_type: Type of sensor for half-life selection
            
        Returns:
            Fused temperature value or None if no valid readings
        """
        if not readings:
            return None
        
        total_weight = 0.0
        weighted_sum = 0.0
        current_time = time.time()
        
        # Get appropriate half-life
        half_life = self._get_half_life(sensor_type, readings)
        
        for sensor_id, value, timestamp in readings:
            # Age factor: exponential decay
            age_seconds = current_time - timestamp
            age_factor = math.exp(-age_seconds / half_life)
            
            # Sensor reliability
            reliability = self.sensor_reliability.get(sensor_id, self.sensor_reliability["default"])
            
            # Combined weight
            weight = reliability * age_factor
            
            weighted_sum += value * weight
            total_weight += weight
        
        if total_weight == 0:
            return None
        
        return weighted_sum / total_weight
    
    def fuse_generic(
        self, 
        readings: List[Tuple[str, float, float]], 
        sensor_type: str = "default"
    ) -> Optional[float]:
        """
        Generic sensor fusion with sensor-type specific half-life.
        
        Args:
            readings: List of (sensor_id, value, timestamp) tuples
            sensor_type: Type of sensor (temperature, co2, occupancy, etc.)
            
        Returns:
            Fused value or None if no valid readings
        """
        return self.fuse_temperature(readings, sensor_type)
    
    def integrate_occupancy(
        self, 
        vision_count: int, 
        pir_active: bool, 
        zone_size: float = 20.0
    ) -> int:
        """
        Integrate occupancy from YOLO vision and PIR sensor.
        
        Args:
            vision_count: Number of people detected by YOLO
            pir_active: PIR motion sensor active
            zone_size: Zone area in square meters
            
        Returns:
            Estimated person count
        """
        estimated_count = vision_count
        
        # If PIR detects motion but YOLO sees no one, someone might be in blind spot
        if pir_active and vision_count == 0:
            estimated_count = 1
        
        # For large zones, compensate for limited camera field of view
        if zone_size > 50 and vision_count > 0:
            # Assume 20% more people outside camera view
            estimated_count = int(vision_count * 1.2)
        
        return estimated_count
