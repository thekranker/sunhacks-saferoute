#!/usr/bin/env python3
"""
Route Sampling Module for Enhanced Street View Analysis

This module provides intelligent sampling of route points for comprehensive
street view safety analysis, ensuring better coverage of the entire route.
"""

import math
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RoutePoint:
    """Represents a point along a route with coordinates and metadata."""
    lat: float
    lng: float
    address: Optional[str] = None
    segment_type: str = "general"  # start, end, intersection, waypoint, general
    weight: float = 1.0  # Importance weight for scoring
    distance_from_start: float = 0.0  # Distance from route start in meters

class RouteSampler:
    """
    Intelligent route sampling for comprehensive street view analysis.
    
    This class provides methods to sample multiple points along a route
    to ensure comprehensive safety analysis coverage.
    """
    
    def __init__(self, max_samples: int = 5, min_distance: float = 100.0):
        """
        Initialize the route sampler.
        
        Args:
            max_samples (int): Maximum number of points to sample
            min_distance (float): Minimum distance between samples in meters
        """
        self.max_samples = max_samples
        self.min_distance = min_distance
        self.logger = logger
    
    def sample_route_points(self, origin_coords: Tuple[float, float], 
                          dest_coords: Tuple[float, float], 
                          route_details: Optional[Dict] = None) -> List[RoutePoint]:
        """
        Sample multiple points along a route for comprehensive analysis.
        
        Args:
            origin_coords: (lat, lng) of route start
            dest_coords: (lat, lng) of route end
            route_details: Additional route information
            
        Returns:
            List of RoutePoint objects to analyze
        """
        try:
            self.logger.info(f"Sampling route from {origin_coords} to {dest_coords}")
            
            # Always include start and end points
            points = [
                RoutePoint(
                    lat=origin_coords[0], 
                    lng=origin_coords[1], 
                    segment_type="start",
                    weight=1.2,  # Higher weight for start/end
                    distance_from_start=0.0
                ),
                RoutePoint(
                    lat=dest_coords[0], 
                    lng=dest_coords[1], 
                    segment_type="end",
                    weight=1.2,
                    distance_from_start=self._calculate_distance(origin_coords, dest_coords)
                )
            ]
            
            # Calculate total route distance
            total_distance = self._calculate_distance(origin_coords, dest_coords)
            self.logger.info(f"Total route distance: {total_distance:.1f} meters")
            
            # Determine sampling strategy based on route length
            if total_distance < 200:  # Short route (< 200m)
                # Just start and end for very short routes
                self.logger.info("Short route - using start and end points only")
                return points
            
            # Calculate number of intermediate points needed
            num_intermediate = min(self.max_samples - 2, max(1, int(total_distance / 300)))
            self.logger.info(f"Adding {num_intermediate} intermediate points")
            
            # Add intermediate points
            for i in range(1, num_intermediate + 1):
                fraction = i / (num_intermediate + 1)
                point = self._interpolate_point(origin_coords, dest_coords, fraction)
                
                # Determine segment type based on position
                segment_type = self._determine_segment_type(fraction, total_distance)
                weight = self._calculate_point_weight(fraction, segment_type)
                
                points.append(RoutePoint(
                    lat=point[0],
                    lng=point[1],
                    segment_type=segment_type,
                    weight=weight,
                    distance_from_start=total_distance * fraction
                ))
            
            # Sort points by distance from start
            points.sort(key=lambda p: p.distance_from_start)
            
            self.logger.info(f"Generated {len(points)} sampling points:")
            for i, point in enumerate(points):
                self.logger.info(f"  Point {i+1}: {point.segment_type} at ({point.lat:.6f}, {point.lng:.6f}) - weight: {point.weight}")
            
            return points
            
        except Exception as e:
            self.logger.error(f"Error sampling route points: {str(e)}")
            # Fallback to just start and end
            return [
                RoutePoint(origin_coords[0], origin_coords[1], segment_type="start", weight=1.0),
                RoutePoint(dest_coords[0], dest_coords[1], segment_type="end", weight=1.0)
            ]
    
    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate distance between two points using Haversine formula."""
        lat1, lng1 = point1
        lat2, lng2 = point2
        
        # Haversine formula
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _interpolate_point(self, start: Tuple[float, float], end: Tuple[float, float], fraction: float) -> Tuple[float, float]:
        """Interpolate a point between start and end based on fraction (0-1)."""
        lat = start[0] + (end[0] - start[0]) * fraction
        lng = start[1] + (end[1] - start[1]) * fraction
        return (lat, lng)
    
    def _determine_segment_type(self, fraction: float, total_distance: float) -> str:
        """Determine the type of route segment based on position and distance."""
        if fraction < 0.1:
            return "start_area"
        elif fraction > 0.9:
            return "end_area"
        elif 0.3 <= fraction <= 0.7:
            return "mid_route"
        else:
            return "transition"
    
    def _calculate_point_weight(self, fraction: float, segment_type: str) -> float:
        """Calculate importance weight for a route point."""
        base_weight = 1.0
        
        # Adjust weight based on segment type
        if segment_type in ["start", "end"]:
            return 1.2  # Start and end are most important
        elif segment_type == "mid_route":
            return 1.1  # Middle sections are important for overall assessment
        elif segment_type == "start_area":
            return 1.05  # Near start
        elif segment_type == "end_area":
            return 1.05  # Near end
        else:
            return 1.0  # Transition areas
    
    def create_location_info(self, point: RoutePoint, route_context: Dict) -> Dict:
        """
        Create location info dictionary for street view analysis.
        
        Args:
            point: RoutePoint to analyze
            route_context: Additional context about the route
            
        Returns:
            Dictionary with location information for street view analysis
        """
        return {
            "address": point.address or f"Route point at {point.lat:.6f}, {point.lng:.6f}",
            "coordinates": f"{point.lat},{point.lng}",
            "time_context": "day",  # Could be made configurable
            "segment_type": point.segment_type,
            "weight": point.weight,
            "distance_from_start": point.distance_from_start,
            "route_context": route_context
        }

def sample_route_for_analysis(origin_coords: Tuple[float, float], 
                            dest_coords: Tuple[float, float], 
                            route_details: Optional[Dict] = None,
                            max_samples: int = 5) -> List[Dict]:
    """
    Convenience function to sample a route for comprehensive analysis.
    
    Args:
        origin_coords: (lat, lng) of route start
        dest_coords: (lat, lng) of route end  
        route_details: Additional route information
        max_samples: Maximum number of points to sample
        
    Returns:
        List of location info dictionaries for street view analysis
    """
    sampler = RouteSampler(max_samples=max_samples)
    points = sampler.sample_route_points(origin_coords, dest_coords, route_details)
    
    route_context = {
        "origin": f"{origin_coords[0]},{origin_coords[1]}",
        "destination": f"{dest_coords[0]},{dest_coords[1]}",
        "total_points": len(points)
    }
    
    return [sampler.create_location_info(point, route_context) for point in points]

if __name__ == "__main__":
    # Test the route sampler
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test with a sample route
    origin = (33.4255, -111.9400)  # ASU Tempe
    destination = (33.4484, -111.9250)  # Downtown Tempe
    
    sampler = RouteSampler(max_samples=5)
    points = sampler.sample_route_points(origin, destination)
    
    print(f"Generated {len(points)} sampling points:")
    for i, point in enumerate(points):
        print(f"  {i+1}. {point.segment_type} at ({point.lat:.6f}, {point.lng:.6f}) - weight: {point.weight}")
