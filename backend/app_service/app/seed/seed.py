import uuid, random, asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, text

from app.database import async_session, create_tables, engine
from app.models.crm import Customer, Order, Product, Segment, SegmentSnapshot
from app.models.campaign import Campaign, CampaignVariant, MarketingGoal, CampaignOpportunity
from app.models.analytics import CampaignPerformance, ChannelPerformance

PRODUCT_CATEGORIES = {
    "Electronics": ["Mobile Phones", "Laptops", "Tablets", "Headphones", "Smartwatches"],
    "Fashion": ["Men's Clothing", "Women's Clothing", "Footwear", "Accessories"],
    "Home & Kitchen": ["Kitchen Appliances", "Home Decor", "Furniture", "Lighting"],
    "Beauty": ["Skincare", "Makeup", "Fragrances", "Hair Care"],
    "Sports": ["Fitness Equipment", "Sportswear", "Outdoor Gear", "Cycling"],
}
FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Ananya", "Diya", "Myra", "Isha", "Aanya",
               "Raj", "Amit", "Priya", "Sunita", "Vikram", "Neha", "Rahul", "Pooja", "Sanjay", "Meera"]
LAST_NAMES = ["Sharma", "Verma", "Patel", "Gupta", "Singh", "Kumar", "Reddy", "Joshi", "Nair", "Desai"]
CITIES = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad", "Jaipur"]
CHANNELS = ["whatsapp", "email", "sms", "rcs"]


def random_date(y1=2023, y2=2025):
    start, end = datetime(y1, 1, 1), datetime(y2, 12, 31)
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))


def rfm_score():
    return f"{random.randint(1,5)}-{random.randint(1,5)}-{random.randint(1,5)}"


def lifecycle(rfm):
    r, f, m = map(int, rfm.split("-"))
    if r >= 4 and f >= 4 and m >= 4: return "champion"
    if r >= 3 and f >= 3 and m >= 3: return "loyal"
    if r >= 3 and f >= 2: return "active"
    if r < 3 and f < 3: return "churned" if r < 2 else "at_risk"
    return "new"


async def seed():
    print("Seeding database...")
    async with engine.begin() as conn:
        for schema in ["crm", "analytics", "system"]:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    await create_tables()

    async with async_session() as db:
        if (await db.execute(select(Product).limit(1))).scalar_one_or_none():
            print("Already seeded."); return

        products = []
        for cat, subcats in PRODUCT_CATEGORIES.items():
            for sub in subcats:
                for i in range(random.randint(1, 2)):
                    p = Decimal(str(round(random.uniform(99, 9999), 2)))
                    products.append(Product(name=f"{sub} {random.choice(['Pro','Lite','Max','Ultra','Premium'])}",
                                            sku=f"{cat[:3].upper()}-{sub[:3].upper()}-{i+1:03d}",
                                            category=cat, subcategory=sub, price=p, cost=p * Decimal(str(round(random.uniform(0.4, 0.7), 2)))))
        db.add_all(products); await db.flush()
        print(f"Products: {len(products)}")

        customers = []
        for i in range(10000):
            first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            rfm = rfm_score(); ls = lifecycle(rfm)
            num_orders = random.randint(0, 25)
            aov = Decimal(str(round(random.uniform(500, 5000), 2)))
            total = aov * num_orders
            ds = random.randint(0, 180) if num_orders > 0 else None
            lo = (datetime.utcnow() - timedelta(days=ds)) if ds else None
            fo = random_date() if num_orders > 0 else None
            customers.append(Customer(external_id=f"CUST-{i+1:05d}", first_name=first, last_name=last,
                                       email=f"{first.lower()}.{last.lower()}.{i+1}@email.com",
                                       phone=f"+91{random.randint(7000000000, 9999999999)}",
                                       city=random.choice(CITIES), country="India",
                                       tags=random.sample(["vip","new","repeat","high_value"], random.randint(0, 2)),
                                       total_orders=num_orders, total_spent=total, average_order_value=aov,
                                       first_order_date=fo, last_order_date=lo, days_since_last_order=ds,
                                       lifecycle_stage=ls, rfm_score=rfm, is_active=random.random() > 0.15))
        db.add_all(customers); await db.flush()
        print(f"Customers: {len(customers)}")

        orders = []
        for cust in customers:
            if cust.total_orders > 0:
                for _ in range(min(cust.total_orders, random.randint(1, 5))):
                    p = random.choice(products); q = random.randint(1, 3)
                    orders.append(Order(customer_id=cust.id, order_date=random_date(),
                                        total_amount=p.price * q, status=random.choice(["completed","completed","completed","returned"]),
                                        product_id=p.id, quantity=q, channel=random.choice(CHANNELS)))
        db.add_all(orders); await db.flush()
        print(f"Orders: {len(orders)}")

        seg_configs = [
            {"name": "High-Value Champions", "criteria": {"lifecycle_stage": "champion", "min_spent": 10000}},
            {"name": "Loyal Regulars", "criteria": {"lifecycle_stage": "loyal", "min_orders": 3}},
            {"name": "At-Risk Customers", "criteria": {"lifecycle_stage": "at_risk", "min_days_since_order": 30}},
            {"name": "New Customers", "criteria": {"lifecycle_stage": "new", "max_orders": 1}},
            {"name": "VIP Segment", "criteria": {"min_spent": 25000, "min_orders": 5}},
            {"name": "Reactivation Prospects", "criteria": {"lifecycle_stage": "churned", "max_days_since_order": 90}},
        ]
        segments = []
        for sc in seg_configs:
            seg = Segment(name=sc["name"], criteria=sc["criteria"], customer_count=random.randint(500, 2000))
            db.add(seg); segments.append(seg)
        await db.flush()

        goal = MarketingGoal(description="Increase repeat purchases among inactive customers", objective="reactivation")
        db.add(goal); await db.flush()

        campaigns = []
        for i, cd in enumerate([{"name":"Festive Sale 2025","channel":"email","status":"completed","expected_reach":5000,"expected_revenue":125000},
                                 {"name":"VIP Exclusive","channel":"whatsapp","status":"completed","expected_reach":1200,"expected_revenue":85000},
                                 {"name":"Flash Sale","channel":"sms","status":"launched","expected_reach":8000,"expected_revenue":45000},
                                 {"name":"Loyalty Rewards","channel":"email","status":"draft","expected_reach":3500,"expected_revenue":65000}]):
            c = Campaign(name=cd["name"], goal_id=goal.id, segment_id=segments[i % len(segments)].id,
                          channel=cd["channel"], status=cd["status"], expected_reach=cd["expected_reach"],
                          expected_revenue=Decimal(str(cd["expected_revenue"])),
                          approval_status="approved" if cd["status"] != "draft" else "pending")
            db.add(c); await db.flush(); campaigns.append(c)
            for j, (vl, st) in enumerate(zip(["A","B","C"][:random.randint(2,3)], ["emotional","urgency","social_proof"])):
                db.add(CampaignVariant(campaign_id=c.id, name=f"Variant {vl}", variant_type=vl,
                                       subject_line=f"Check out our offers!", message_body=f"Hey {{first_name}}, check this out!",
                                       style=st, traffic_allocation=33))
            if cd["status"] == "completed":
                sent = random.randint(1000, 5000); d = int(sent * random.uniform(0.85, 0.98))
                o = int(d * random.uniform(0.15, 0.45)); cl = int(o * random.uniform(0.20, 0.50))
                cv = int(cl * random.uniform(0.05, 0.15))
                db.add(CampaignPerformance(campaign_id=c.id, sent_count=sent, delivered_count=d, open_count=o,
                                            click_count=cl, conversion_count=cv,
                                            revenue=Decimal(str(round(cv * random.uniform(500, 2000), 2))),
                                            delivery_rate=round(d/sent*100,2), open_rate=round(o/d*100,2),
                                            click_through_rate=round(cl/o*100,2), conversion_rate=round(cv/cl*100,2)))
        await db.flush()
        print(f"Campaigns: {len(campaigns)}")

        for i, od in enumerate([{"title":"Festival Season Campaign","type":"seasonal_promotion","revenue":125000,"reach":8500},
                                 {"title":"At-Risk Reactivation","type":"churn_prevention","revenue":45000,"reach":2340},
                                 {"title":"Cross-sell Accessories","type":"cross_sell","revenue":32000,"reach":3456}]):
            db.add(CampaignOpportunity(title=od["title"], opportunity_type=od["type"],
                                        expected_revenue=Decimal(str(od["revenue"])), expected_reach=od["reach"],
                                        recommended_channel=random.choice(CHANNELS),
                                        status="pending" if i > 0 else "approved"))
        for ch in CHANNELS:
            sent = random.randint(5000, 20000)
            db.add(ChannelPerformance(channel=ch, sent_count=sent, delivered_count=int(sent*random.uniform(0.85,0.99)),
                                       open_count=int(sent*random.uniform(0.10,0.35)),
                                       click_count=int(sent*random.uniform(0.03,0.12)),
                                       conversion_count=int(sent*random.uniform(0.005,0.03)),
                                       revenue=Decimal(str(round(sent*random.uniform(10,50),2))),
                                       period_start=datetime.utcnow()-timedelta(days=30), period_end=datetime.utcnow()))
        await db.commit()
        print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
