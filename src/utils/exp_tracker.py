'''
EXP Tracking Module
Tracks EXP changes over time using snapshot-based approach
Records snapshots every 60 seconds and calculates gains from differences
'''
import time
import threading
from collections import deque
from typing import Dict, List, Optional
import json
import os
from datetime import datetime


class ExpSnapshot:
    """Represents an EXP snapshot at a specific time"""
    def __init__(self, timestamp: float, exp_percent: float):
        self.timestamp = timestamp
        self.exp_percent = round(exp_percent, 1)  # Round to 1 decimal place
        self.datetime_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        self.time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M')
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'exp_percent': self.exp_percent,
            'datetime': self.datetime_str,
            'time': self.time_str
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(data['timestamp'], data['exp_percent'])


class ExpTracker:
    def __init__(self, max_history_hours=24, snapshot_interval=60):
        """
        Initialize EXP tracker with snapshot-based recording
        
        Args:
            max_history_hours: Maximum hours of history to keep in memory
            snapshot_interval: Interval in seconds to take snapshots (default 60s)
        """
        self.max_history_hours = max_history_hours
        self.max_history_seconds = max_history_hours * 3600
        self.snapshot_interval = snapshot_interval
        
        # Snapshot storage: List of ExpSnapshot objects, ordered by time
        self.snapshots = deque(maxlen=max_history_hours * 60)  # 60 snapshots per hour max
        
        # Thread safety
        self.data_lock = threading.Lock()
        
        # Current EXP tracking
        self.current_exp_percent = None
        self.last_snapshot_time = None
        self.last_update_time = None
        
        # Data persistence
        self.data_file = "exp_tracking_snapshots.json"
        self.load_data()
        
    def update_exp(self, exp_percent: float) -> Optional[float]:
        """
        Update current EXP percentage and take snapshot if needed
        
        Args:
            exp_percent: Current EXP percentage (0-100)
            
        Returns:
            EXP gain since last snapshot (None if no new snapshot)
        """
        current_time = time.time()
        exp_gain = None
        
        # Round to 1 decimal place to avoid floating point precision issues
        exp_percent = round(exp_percent, 1)
        
        with self.data_lock:
            # Always update current values
            self.current_exp_percent = exp_percent
            self.last_update_time = current_time
            
            # Debug: print every update (but limit frequency)
            if not hasattr(self, '_last_debug_time') or current_time - self._last_debug_time > 10:
                self._last_debug_time = current_time
            
            # Check if it's time for a new snapshot
            should_snapshot = (
                self.last_snapshot_time is None or 
                current_time - self.last_snapshot_time >= self.snapshot_interval
            )
            
            if should_snapshot:
                exp_gain = self._take_snapshot(current_time, exp_percent)
                self.last_snapshot_time = current_time
            
            # Clean old snapshots
            self._cleanup_old_data(current_time)
            
        return exp_gain
    
    def _take_snapshot(self, timestamp: float, exp_percent: float) -> Optional[float]:
        """Take a snapshot and calculate gain since last snapshot"""
        new_snapshot = ExpSnapshot(timestamp, exp_percent)
        exp_gain = None
        
        # Calculate gain from previous snapshot
        if len(self.snapshots) > 0:
            prev_snapshot = self.snapshots[-1]
            raw_gain = exp_percent - prev_snapshot.exp_percent
            
            # Handle level up (EXP resets to near 0)
            if raw_gain < -50:  # Likely a level up
                exp_gain = (100 - prev_snapshot.exp_percent) + exp_percent
                print(f"[ExpTracker] Level up detected! Gain: {exp_gain:.1f}% "
                      f"(from {prev_snapshot.exp_percent:.1f}% to {exp_percent:.1f}%)")
            elif raw_gain > 0:
                exp_gain = raw_gain
                print(f"[ExpTracker] Snapshot recorded: {exp_gain:.1f}% gain "
                      f"(from {prev_snapshot.exp_percent:.1f}% to {exp_percent:.1f}%) "
                      f"at {new_snapshot.datetime_str}")
            elif raw_gain == 0:
                exp_gain = 0.0
                print(f"[ExpTracker] No EXP change at {new_snapshot.datetime_str}")
            else:
                # Negative gain (likely detection error)
                exp_gain = 0.0
                print(f"[ExpTracker] Ignoring negative change: {raw_gain:.1f}% at {new_snapshot.datetime_str}")
        else:
            print(f"[ExpTracker] First snapshot taken: {exp_percent:.1f}% at {new_snapshot.datetime_str}")
            exp_gain = 0.0  # 首次快照没有增长
        
        # Add to snapshots
        self.snapshots.append(new_snapshot)
        return exp_gain
        
    def _cleanup_old_data(self, current_time: float):
        """Remove snapshots older than max_history_hours"""
        cutoff_time = current_time - self.max_history_seconds
        
        # Remove old snapshots from the front
        while self.snapshots and self.snapshots[0].timestamp < cutoff_time:
            self.snapshots.popleft()
    
    def get_exp_per_minute_data(self, hours_back: int = 1) -> List[Dict]:
        """
        Get EXP gain per minute calculated from snapshot differences
        
        Args:
            hours_back: Number of hours of history to return
            
        Returns:
            List of {'timestamp': int, 'exp_gain': float, 'datetime': str, 'time': str}
        """
        current_time = time.time()
        cutoff_time = current_time - (hours_back * 3600)
        
        with self.data_lock:
            # Filter snapshots within time range
            recent_snapshots = [
                snapshot for snapshot in self.snapshots 
                if snapshot.timestamp >= cutoff_time
            ]
            
            result = []
            
            # Calculate gains between consecutive snapshots
            for i in range(1, len(recent_snapshots)):
                prev_snapshot = recent_snapshots[i-1]
                curr_snapshot = recent_snapshots[i]
                
                # Calculate time difference in minutes
                time_diff_minutes = (curr_snapshot.timestamp - prev_snapshot.timestamp) / 60.0
                
                # Calculate EXP gain
                raw_gain = curr_snapshot.exp_percent - prev_snapshot.exp_percent
                
                # Handle level up
                if raw_gain < -50:
                    exp_gain = (100 - prev_snapshot.exp_percent) + curr_snapshot.exp_percent
                elif raw_gain < 0:
                    exp_gain = 0.0  # Ignore negative changes (detection errors)
                else:
                    exp_gain = raw_gain
                
                # Calculate gain per minute
                exp_gain_per_minute = exp_gain / time_diff_minutes if time_diff_minutes > 0 else 0.0
                
                result.append({
                    'timestamp': int(curr_snapshot.timestamp),
                    'exp_gain': round(exp_gain, 1),
                    'exp_gain_per_minute': round(exp_gain_per_minute, 2),
                    'time_interval_minutes': round(time_diff_minutes, 1),
                    'datetime': curr_snapshot.datetime_str,
                    'time': curr_snapshot.time_str,
                    'prev_exp': prev_snapshot.exp_percent,
                    'curr_exp': curr_snapshot.exp_percent
                })
            
            return result
    
    def get_statistics(self, hours_back: int = 1) -> Dict:
        """
        Get EXP gain statistics based on snapshots
        
        Args:
            hours_back: Number of hours to analyze
            
        Returns:
            Dictionary with statistics
        """
        snapshot_data = self.get_exp_per_minute_data(hours_back)
        
        if not snapshot_data:
            return {
                'total_exp_gain': 0.0,
                'avg_exp_per_minute': 0.0,
                'max_exp_per_minute': 0.0,
                'active_snapshots': 0,
                'total_snapshots': 0,
                'efficiency_percent': 0.0,
                'total_time_minutes': 0.0
            }
        
        gains = [d['exp_gain'] for d in snapshot_data]
        gains_per_minute = [d['exp_gain_per_minute'] for d in snapshot_data]
        total_gain = sum(gains)
        active_snapshots = sum(1 for gain in gains if gain > 0)
        total_time = sum(d['time_interval_minutes'] for d in snapshot_data)
        
        return {
            'total_exp_gain': round(total_gain, 1),
            'avg_exp_per_minute': round(sum(gains_per_minute) / len(gains_per_minute), 2) if gains_per_minute else 0.0,
            'max_exp_per_minute': round(max(gains_per_minute), 2) if gains_per_minute else 0.0,
            'active_snapshots': active_snapshots,
            'total_snapshots': len(snapshot_data),
            'efficiency_percent': round((active_snapshots / len(snapshot_data)) * 100, 1) if snapshot_data else 0.0,
            'total_time_minutes': round(total_time, 1)
        }
    
    def get_current_exp(self) -> Optional[float]:
        """Get the most recent EXP percentage"""
        with self.data_lock:
            return self.current_exp_percent
    
    def get_snapshots_raw(self, hours_back: int = 1) -> List[Dict]:
        """Get raw snapshot data for debugging"""
        current_time = time.time()
        cutoff_time = current_time - (hours_back * 3600)
        
        with self.data_lock:
            return [
                snapshot.to_dict() 
                for snapshot in self.snapshots 
                if snapshot.timestamp >= cutoff_time
            ]
    
    def save_data(self):
        """Save snapshot data to file"""
        with self.data_lock:
            try:
                data = {
                    'snapshots': [snapshot.to_dict() for snapshot in self.snapshots],
                    'current_exp_percent': self.current_exp_percent,
                    'last_snapshot_time': self.last_snapshot_time,
                    'last_update_time': self.last_update_time,
                    'save_time': time.time()
                }
                
                with open(self.data_file, 'w') as f:
                    json.dump(data, f, indent=2)
                    
            except Exception as e:
                print(f"Error saving EXP tracking data: {e}")
    
    def load_data(self):
        """Load snapshot data from file"""
        if not os.path.exists(self.data_file):
            return
            
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            # Check if data is recent (within 24 hours)
            save_time = data.get('save_time', 0)
            if time.time() - save_time > 24 * 3600:
                print("EXP tracking data is too old, starting fresh")
                return
            
            with self.data_lock:
                # Load snapshots
                if 'snapshots' in data:
                    self.snapshots.clear()
                    for snapshot_dict in data['snapshots']:
                        snapshot = ExpSnapshot.from_dict(snapshot_dict)
                        self.snapshots.append(snapshot)
                
                # Load current values
                self.current_exp_percent = data.get('current_exp_percent')
                self.last_snapshot_time = data.get('last_snapshot_time')
                self.last_update_time = data.get('last_update_time')
                
                # Clean old data
                if self.last_update_time:
                    self._cleanup_old_data(time.time())
                    
                print(f"[ExpTracker] Loaded {len(self.snapshots)} snapshots from file")
                    
        except Exception as e:
            print(f"Error loading EXP tracking data: {e}")

    def clear_data(self):
        """Clear all tracking data"""
        with self.data_lock:
            self.snapshots.clear()
            self.current_exp_percent = None
            self.last_snapshot_time = None
            self.last_update_time = None


# Global instance
exp_tracker = ExpTracker()