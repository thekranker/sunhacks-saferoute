#!/usr/bin/env python3
"""
Enhanced Street View Agent for Multi-Point Route Analysis

This module extends the original streetview agent to analyze multiple
points along a route for comprehensive safety assessment.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from gemini_streetview_agent import GeminiStreetViewAgent, analyze_streetview_safety
from route_sampler import RouteSampler, sample_route_for_analysis

logger = logging.getLogger(__name__)

class EnhancedStreetViewAgent:
    """
    Enhanced street view agent that analyzes multiple points along a route
    for comprehensive safety assessment.
    """
    
    def __init__(self, max_concurrent_analysis: int = 3):
        """
        Initialize the enhanced street view agent.
        
        Args:
            max_concurrent_analysis: Maximum number of concurrent analyses
        """
        self.max_concurrent_analysis = max_concurrent_analysis
        self.base_agent = GeminiStreetViewAgent()
        self.logger = logger
    
    def analyze_route_comprehensive(self, origin_coords: Tuple[float, float], 
                                 dest_coords: Tuple[float, float], 
                                 route_details: Optional[Dict] = None,
                                 max_samples: int = 5) -> Dict:
        """
        Perform comprehensive route analysis by sampling multiple points.
        
        Args:
            origin_coords: (lat, lng) of route start
            dest_coords: (lat, lng) of route end
            route_details: Additional route information
            max_samples: Maximum number of points to sample
            
        Returns:
            Comprehensive analysis results with weighted scoring
        """
        try:
            self.logger.info("=" * 80)
            self.logger.info("ENHANCED STREET VIEW AGENT - COMPREHENSIVE ROUTE ANALYSIS")
            self.logger.info("=" * 80)
            self.logger.info(f"Analyzing route from {origin_coords} to {dest_coords}")
            
            # Sample multiple points along the route
            sampling_points = sample_route_for_analysis(
                origin_coords, dest_coords, route_details, max_samples
            )
            
            self.logger.info(f"Sampled {len(sampling_points)} points for analysis")
            
            # Analyze each point
            analysis_results = []
            successful_analyses = 0
            total_weight = 0.0
            weighted_score_sum = 0.0
            
            for i, location_info in enumerate(sampling_points):
                self.logger.info(f"Analyzing point {i+1}/{len(sampling_points)}: {location_info['segment_type']}")
                
                try:
                    # Analyze this specific point
                    result = analyze_streetview_safety(None, location_info)
                    
                    if result.get("success", False):
                        analysis_results.append({
                            "point_index": i,
                            "location_info": location_info,
                            "analysis": result,
                            "weight": location_info.get("weight", 1.0)
                        })
                        
                        # Calculate weighted score
                        weight = location_info.get("weight", 1.0)
                        score = result.get("safety_score", 0)
                        weighted_score_sum += score * weight
                        total_weight += weight
                        successful_analyses += 1
                        
                        self.logger.info(f"  Point {i+1} analysis successful: {score}% (weight: {weight})")
                    else:
                        self.logger.warning(f"  Point {i+1} analysis failed: {result.get('error', 'Unknown error')}")
                        analysis_results.append({
                            "point_index": i,
                            "location_info": location_info,
                            "analysis": result,
                            "weight": location_info.get("weight", 1.0),
                            "failed": True
                        })
                        
                except Exception as e:
                    self.logger.error(f"  Point {i+1} analysis error: {str(e)}")
                    analysis_results.append({
                        "point_index": i,
                        "location_info": location_info,
                        "analysis": {"success": False, "error": str(e)},
                        "weight": location_info.get("weight", 1.0),
                        "failed": True
                    })
            
            # Calculate comprehensive results
            if successful_analyses > 0:
                final_score = round(weighted_score_sum / total_weight, 1)
                confidence_level = self._calculate_confidence_level(successful_analyses, len(sampling_points))
            else:
                final_score = 0
                confidence_level = "low"
            
            # Aggregate concerns and recommendations
            all_concerns = []
            all_recommendations = []
            all_positive_factors = []
            metric_breakdowns = []
            
            for result in analysis_results:
                if not result.get("failed", False) and result["analysis"].get("success", False):
                    analysis = result["analysis"]
                    
                    # Collect concerns and recommendations
                    if analysis.get("key_concerns"):
                        for concern in analysis["key_concerns"]:
                            all_concerns.append(f"[{result['location_info']['segment_type']}] {concern}")
                    
                    if analysis.get("recommendations"):
                        for rec in analysis["recommendations"]:
                            all_recommendations.append(f"[{result['location_info']['segment_type']}] {rec}")
                    
                    if analysis.get("positive_factors"):
                        for factor in analysis["positive_factors"]:
                            all_positive_factors.append(f"[{result['location_info']['segment_type']}] {factor}")
                    
                    # Collect metric breakdowns for analysis
                    if analysis.get("metric_breakdown"):
                        metric_breakdowns.append(analysis["metric_breakdown"])
            
            # Create comprehensive analysis result
            comprehensive_result = {
                "success": successful_analyses > 0,
                "comprehensive_safety_score": final_score,
                "confidence_level": confidence_level,
                "analysis_type": "comprehensive_multi_point",
                "points_analyzed": successful_analyses,
                "total_points_sampled": len(sampling_points),
                "coverage_percentage": round((successful_analyses / len(sampling_points)) * 100, 1),
                "route_analysis": {
                    "origin": f"{origin_coords[0]},{origin_coords[1]}",
                    "destination": f"{dest_coords[0]},{dest_coords[1]}",
                    "total_distance_estimated": self._estimate_route_distance(origin_coords, dest_coords),
                    "sampling_strategy": "intelligent_weighted"
                },
                "aggregated_concerns": self._deduplicate_items(all_concerns),
                "aggregated_recommendations": self._deduplicate_items(all_recommendations),
                "aggregated_positive_factors": self._deduplicate_items(all_positive_factors),
                "detailed_results": analysis_results,
                "analysis_timestamp": datetime.now().isoformat(),
                "enhancement_notes": self._generate_enhancement_notes(analysis_results, successful_analyses)
            }
            
            # Log comprehensive results
            self._log_comprehensive_analysis(comprehensive_result)
            
            return comprehensive_result
            
        except Exception as e:
            self.logger.error(f"Comprehensive route analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "comprehensive_safety_score": 0,
                "confidence_level": "low",
                "analysis_type": "failed"
            }
    
    def _calculate_confidence_level(self, successful_analyses: int, total_points: int) -> str:
        """Calculate confidence level based on successful analyses."""
        success_rate = successful_analyses / total_points if total_points > 0 else 0
        
        if success_rate >= 0.8:
            return "high"
        elif success_rate >= 0.6:
            return "medium"
        else:
            return "low"
    
    def _estimate_route_distance(self, origin: Tuple[float, float], dest: Tuple[float, float]) -> float:
        """Estimate route distance using Haversine formula."""
        from route_sampler import RouteSampler
        sampler = RouteSampler()
        return sampler._calculate_distance(origin, dest)
    
    def _deduplicate_items(self, items: List[str]) -> List[str]:
        """Remove duplicate items while preserving order."""
        seen = set()
        unique_items = []
        for item in items:
            if item not in seen:
                seen.add(item)
                unique_items.append(item)
        return unique_items
    
    def _generate_enhancement_notes(self, analysis_results: List[Dict], successful_analyses: int) -> str:
        """Generate notes about the enhanced analysis."""
        total_points = len(analysis_results)
        success_rate = (successful_analyses / total_points) * 100 if total_points > 0 else 0
        
        notes = f"Enhanced multi-point analysis: {successful_analyses}/{total_points} points analyzed ({success_rate:.1f}% success rate). "
        
        if successful_analyses > 1:
            notes += "Comprehensive route coverage achieved with weighted scoring across multiple segments. "
        else:
            notes += "Limited coverage - consider route-specific factors. "
        
        # Add segment-specific insights
        segment_types = [r["location_info"]["segment_type"] for r in analysis_results if not r.get("failed", False)]
        if segment_types:
            unique_segments = set(segment_types)
            notes += f"Analyzed segments: {', '.join(unique_segments)}."
        
        return notes
    
    def _log_comprehensive_analysis(self, result: Dict):
        """Log the comprehensive analysis results."""
        self.logger.info("=" * 80)
        self.logger.info("COMPREHENSIVE ROUTE ANALYSIS COMPLETE")
        self.logger.info("=" * 80)
        
        if result.get("success", False):
            self.logger.info(f"Comprehensive Safety Score: {result['comprehensive_safety_score']}%")
            self.logger.info(f"Confidence Level: {result['confidence_level']}")
            self.logger.info(f"Points Analyzed: {result['points_analyzed']}/{result['total_points_sampled']}")
            self.logger.info(f"Coverage: {result['coverage_percentage']}%")
            
            if result.get("aggregated_concerns"):
                self.logger.info("Key Route Concerns:")
                for concern in result["aggregated_concerns"][:5]:  # Top 5 concerns
                    self.logger.info(f"  - {concern}")
            
            if result.get("aggregated_recommendations"):
                self.logger.info("Route Safety Recommendations:")
                for rec in result["aggregated_recommendations"][:5]:  # Top 5 recommendations
                    self.logger.info(f"  - {rec}")
            
            self.logger.info(f"Enhancement Notes: {result.get('enhancement_notes', 'N/A')}")
        else:
            self.logger.error("Comprehensive analysis failed")
            self.logger.error(f"Error: {result.get('error', 'Unknown error')}")
        
        self.logger.info("=" * 80)

def analyze_route_comprehensive(origin_coords: Tuple[float, float], 
                              dest_coords: Tuple[float, float], 
                              route_details: Optional[Dict] = None,
                              max_samples: int = 5) -> Dict:
    """
    Convenience function for comprehensive route analysis.
    
    Args:
        origin_coords: (lat, lng) of route start
        dest_coords: (lat, lng) of route end
        route_details: Additional route information
        max_samples: Maximum number of points to sample
        
    Returns:
        Comprehensive analysis results
    """
    agent = EnhancedStreetViewAgent()
    return agent.analyze_route_comprehensive(origin_coords, dest_coords, route_details, max_samples)

if __name__ == "__main__":
    # Test the enhanced street view agent
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test with a sample route
    origin = (33.4255, -111.9400)  # ASU Tempe
    destination = (33.4484, -111.9250)  # Downtown Tempe
    
    result = analyze_route_comprehensive(origin, destination, max_samples=5)
    
    if result.get("success", False):
        print(f"Comprehensive Safety Score: {result['comprehensive_safety_score']}%")
        print(f"Points Analyzed: {result['points_analyzed']}/{result['total_points_sampled']}")
        print(f"Coverage: {result['coverage_percentage']}%")
    else:
        print(f"Analysis failed: {result.get('error', 'Unknown error')}")
