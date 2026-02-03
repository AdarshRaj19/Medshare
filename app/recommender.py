"""
AI-Powered Recommendation System for MedShare
Uses collaborative filtering and content-based recommendations
"""

from django.db.models import Q, Avg, Count, F
from .models import Medicine, DonationRequest, MedicineRating, MedicineSearchLog
from datetime import date, timedelta
import math


class MedicineRecommender:
    """Recommends medicines based on user behavior and medicine characteristics"""

    def __init__(self, user):
        self.user = user
        self.min_rating_threshold = 2.0  # Minimum rating to consider

    def get_personalized_recommendations(self, limit=6):
        """
        Get personalized medicine recommendations for a user
        Combines multiple recommendation strategies
        """
        if self.user.profile.role == 'donor':
            return self.get_donor_insights()
        else:
            return self.get_ngo_recommendations(limit)

    def get_ngo_recommendations(self, limit=6):
        """
        Recommendations for NGOs based on:
        1. Request history
        2. Similar medicines with high ratings
        3. Expiring medicines nearby
        """
        
        # Get medicines user has requested before
        requested_medicines = list(
            DonationRequest.objects.filter(requester=self.user, requester_type='ngo').values_list("medicine_id", flat=True)
        )

        # Get medicines NGO has rated highly
        highly_rated = MedicineRating.objects.filter(
            user=self.user,
            rating__gte=4
        ).select_related('medicine')

        recommendations = []

        # Strategy 1: Similar medicines to highly rated ones
        if highly_rated.exists():
            liked_medicines = [r.medicine for r in highly_rated]
            for med in liked_medicines:
                similar = Medicine.objects.filter(
                    status='available',
                    name__icontains=med.name.split()[0],  # Match first word
                ).exclude(id__in=requested_medicines).exclude(id=med.id).annotate(
                    avg_rating=Avg('ratings__rating')
                ).filter(
                    avg_rating__gte=self.min_rating_threshold
                )[:2]
                recommendations.extend(list(similar))

        # Strategy 2: Highly rated medicines
        if not recommendations:
            recommendations = list(
                Medicine.objects.filter(
                    status='available'
                ).annotate(
                    avg_rating=Avg('ratings__rating'),
                    rating_count=Count('ratings')
                ).filter(
                    avg_rating__gte=self.min_rating_threshold,
                    rating_count__gt=0
                ).exclude(id__in=requested_medicines).order_by('-avg_rating')[:6]
            )

        # Strategy 3: Medicines expiring soon (urgent)
        cutoff_date = date.today() + timedelta(days=14)
        urgent = list(
            Medicine.objects.filter(
                status='available',
                expiry_date__lte=cutoff_date,
                expiry_date__gt=date.today(),
            ).exclude(id__in=requested_medicines).annotate(
                avg_rating=Avg('ratings__rating')
            ).order_by('-avg_rating')[:3]
        )
        recommendations.extend(urgent)

        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for med in recommendations:
            if med.id not in seen:
                seen.add(med.id)
                unique_recommendations.append(med)

        return unique_recommendations[:limit]

    def get_donor_insights(self):
        """
        Insights for donors:
        1. Most requested medicines
        2. Top-rated medicines to highlight
        3. Similar medicines to their donations
        """
        donated = Medicine.objects.filter(donor=self.user)
        
        # Get medicines with highest demand (most requests)
        most_requested = Medicine.objects.filter(
            status='available'
        ).annotate(
            request_count=Count('requests')
        ).filter(
            request_count__gt=0
        ).order_by('-request_count')[:6]

        return list(most_requested)

    def calculate_recommendation_score(self, medicine):
        """
        Calculate a recommendation score for a medicine (0-100)
        Based on:
        - Rating (40%)
        - Recency of requests (30%)
        - Availability (20%)
        - Distance to user (10%)
        """
        score = 0

        # Rating score (0-40)
        if medicine.rating > 0:
            rating_score = (medicine.rating / 5) * 40
            score += rating_score

        # Request recency (0-30)
        recent_requests = DonationRequest.objects.filter(
            medicine=medicine
        ).order_by('-created_at').first()

        if recent_requests:
            days_since_request = (date.today() - recent_requests.created_at.date()).days
            recency_score = max(0, 30 - (days_since_request * 0.5))
            score += recency_score

        # Availability (0-20)
        if medicine.status == 'available':
            score += 20

        # Distance score (0-10)
        if self.user.profile.latitude and self.user.profile.longitude:
            if medicine.latitude and medicine.longitude:
                distance = self.calculate_distance(
                    self.user.profile.latitude,
                    self.user.profile.longitude,
                    medicine.latitude,
                    medicine.longitude
                )
                # Closer = higher score
                distance_score = max(0, 10 - (distance / 10))
                score += distance_score

        return round(min(100, score), 2)

    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """
        Calculate distance in kilometers using Haversine formula
        """
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c

    def log_search(self, query, results):
        """Log search for analytics and recommendation training"""
        search_log = MedicineSearchLog.objects.create(
            user=self.user,
            search_query=query
        )
        search_log.medicine_results.set(results[:10])
        return search_log

    @staticmethod
    def get_trending_medicines(limit=5):
        """
        Get trending medicines based on recent request activity
        """
        trending = Medicine.objects.filter(
            status='available'
        ).annotate(
            recent_requests=Count(
                'requests',
                filter=Q(
                    requests__created_at__gte=date.today() - timedelta(days=7)
                )
            ),
            avg_rating=Avg('ratings__rating')
        ).filter(
            recent_requests__gt=0
        ).order_by('-recent_requests', '-avg_rating')[:limit]

        return list(trending)

    @staticmethod
    def get_expiring_soon_medicines(days=30, limit=10):
        """
        Get medicines expiring soon (within N days)
        Urgent for NGOs to request
        """
        cutoff_date = date.today() + timedelta(days=days)
        
        expiring = Medicine.objects.filter(
            status='available',
            expiry_date__lte=cutoff_date,
            expiry_date__gt=date.today()
        ).annotate(
            avg_rating=Avg('ratings__rating')
        ).order_by('expiry_date')[:limit]

        return list(expiring)


def update_recommendation_scores():
    """
    Batch update recommendation scores for all medicines
    Should be run periodically (e.g., daily via Celery)
    """
    medicines = Medicine.objects.all()
    
    for medicine in medicines:
        # Calculate score based on multiple factors
        score = 0
        
        # Rating contribution (40%)
        avg_rating = medicine.ratings.aggregate(avg=Avg('rating'))['avg'] or 0
        score += (avg_rating / 5) * 40
        
        # Recent requests (30%)
        recent_count = medicine.requests.filter(
            created_at__gte=date.today() - timedelta(days=7)
        ).count()
        score += min(30, recent_count * 5)
        
        # Availability (20%)
        if medicine.status == 'available':
            score += 20
        
        # Freshness (10%)
        days_old = (date.today() - medicine.created_at.date()).days
        freshness_score = max(0, 10 - (days_old * 0.05))
        score += freshness_score
        
        medicine.recommendation_score = round(min(100, score), 2)
        medicine.save()
