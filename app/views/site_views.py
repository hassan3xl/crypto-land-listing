from django.shortcuts import render
from django.db.models import Sum, Count, Q
from app.models import LandListing, Transaction, ZoningType, User


def home(request):
    """Homepage view showcasing featured properties, hero search, market stats, and platform features."""
    featured_lands = LandListing.objects.filter(
        status=LandListing.Status.AVAILABLE,
        is_featured=True
    )[:6]
    
    recent_lands = LandListing.objects.filter(
        status=LandListing.Status.AVAILABLE
    ).order_by('-created_at')[:6]
    
    # Calculate stats
    total_lands = LandListing.objects.filter(status=LandListing.Status.AVAILABLE).count()
    verified_deeds = LandListing.objects.filter(deed_verified=True).count()
    total_sellers = User.objects.filter(role='seller').count()
    completed_txs = Transaction.objects.filter(status=Transaction.Status.COMPLETED).count()
    
    context = {
        'featured_lands': featured_lands,
        'recent_lands': recent_lands,
        'zoning_types': ZoningType.choices,
        'stats': {
            'total_lands': total_lands,
            'verified_deeds': verified_deeds,
            'total_sellers': total_sellers,
            'completed_txs': completed_txs,
        }
    }
    return render(request, 'app/home.html', context)
