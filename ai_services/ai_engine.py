from .models import Scheme

def recommend_schemes_for_farmer(farmer_profile, active_crops=None, total_land=0):
    """
    Farmer profile aur crops ke data ke hisaab se eligible aur best-match 
    schemes calculate karta hai.
    """
    schemes = Scheme.objects.filter(is_active=True)
    recommended_list = []

    user_state = farmer_profile.state if farmer_profile else "Madhya Pradesh"
    crop_names = [c.name.lower() for c in active_crops] if active_crops else []

    for s in schemes:
        score = 0
        match_reasons = []

        # 1. State matching
        if s.state == "All India" or user_state.lower() in s.state.lower():
            score += 30
            match_reasons.append(f"Available in your region ({s.state})")
        else:
            continue  # State match nahi to skip

        # 2. Land Area eligibility
        if float(s.min_land_acres) <= float(total_land) <= float(s.max_land_acres):
            score += 35
            match_reasons.append(f"Land criteria matched ({total_land} Acres)")

        # 3. Crop specificity matching
        target_crops = [x.strip().lower() for x in s.target_crops.split(',')]
        if 'all' in target_crops:
            score += 20
        else:
            matched_crops = [cn for cn in crop_names if any(tc in cn for tc in target_crops)]
            if matched_crops:
                score += 35
                match_reasons.append(f"Matched with standing crop: {', '.join(matched_crops).title()}")

        # 4. Financial Benefit High-Weight
        if s.subsidy_percentage >= 50 or s.max_benefit_amount >= 10000:
            score += 15

        # Normalize score
        final_score = min(98, score)

        if final_score >= 50:
            recommended_list.append({
                'scheme': s,
                'match_percentage': final_score,
                'reasons': match_reasons,
                'estimated_savings': s.max_benefit_amount,
            })

    # Sort by highest AI match
    recommended_list.sort(key=lambda x: x['match_percentage'], reverse=True)
    return recommended_list