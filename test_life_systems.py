"""Headless integration tests for Life Simulator life systems.
Run: python test_life_systems.py
"""
import sys, os, json, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_data import GameData
from health_manager import HealthManager
from housing_manager import HousingManager
from education_manager import EducationManager
from social_manager import SocialManager

PASS = 0
FAIL = 0

def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  OK   {label}" + (f" ({detail})" if detail else ""))
    else:
        FAIL += 1
        print(f"  FAIL {label}" + (f" -- {detail}" if detail else ""))


# === 1. GameData Persistence ===
print("\n=== 1. GameData Persistence ===")
data = GameData()
check("health field exists", hasattr(data, 'health'))
check("housing field exists", hasattr(data, 'housing'))
check("education field exists", hasattr(data, 'education'))
check("social field exists", hasattr(data, 'social'))
check("health.energy=100", data.health['energy'] == 100)
check("housing.type=rent", data.housing['type'] == '租屋')
check("education.degree=high_school", data.education['degree'] == '高中')
check("social.reputation=10", data.social['reputation'] == 10)

# Save and reload
tmp = tempfile.mktemp(suffix='.json')
try:
    data.save(tmp)
    d2 = GameData()
    d2.load(tmp)
    check("reloaded energy=100", d2.health['energy'] == 100)
    check("reloaded housing=rent", d2.housing['type'] == '租屋')
    d2.health['energy'] = 50
    d2.housing['type'] = '公寓'
    d2.save(tmp)
    d3 = GameData()
    d3.load(tmp)
    check("reloaded energy=50", d3.health['energy'] == 50)
    check("reloaded housing=apartment", d3.housing['type'] == '公寓')
finally:
    os.unlink(tmp)


# === 2. Health System ===
print("\n=== 2. Health System ===")
data = GameData()
hm = HealthManager(data)

check("initial energy=100", data.health['energy'] == 100)
check("initial mood=70", data.health['mood'] == 70)

# Eat meal
old_cash = data.cash
hm.eat_meal(2)
check("cash deducted 150", data.cash == old_cash - 150, f"cash={data.cash}")
check("mood up after eating", data.health['mood'] > 70, f"mood={data.health['mood']}")
check("nutrition up", data.health['nutrition'] > 50, f"nut={data.health['nutrition']}")

# Exercise
old_e = data.health['energy']
old_f = data.health['fitness']
hm.exercise()
check("exercise costs energy", data.health['energy'] < old_e, f"energy={data.health['energy']}")
check("fitness up", data.health['fitness'] > old_f, f"fit={data.health['fitness']}")

# Rest
old_e2 = data.health['energy']
hm.rest()
check("rest recovers energy", data.health['energy'] > old_e2, f"energy={data.health['energy']}")

# Meditate
old_s = data.health['stress']
hm.meditate()
check("meditate reduces stress", data.health['stress'] < old_s, f"stress={data.health['stress']}")

# No cash eat
data.cash = 0
msg = hm.eat_meal(1)
check("eat fails no cash", "不足" in msg)

# Sick blocks exercise
data.health['sick_days'] = 2
msg = hm.exercise()
check("exercise blocked sick", "生病" in msg)
data.health['sick_days'] = 0

# Efficiency
data.health['stress'] = 10
data.health['energy'] = 80
data.health['health_points'] = 80
mod = hm.efficiency_modifier()
check("healthy mod >= 1.0", mod >= 1.0, f"mod={mod}")

data.health['stress'] = 80
mod = hm.efficiency_modifier()
check("stressed mod < 1.0", mod < 1.0, f"mod={mod}")

data.health['sick_days'] = 1
mod = hm.efficiency_modifier()
check("sick mod < 0.8", mod < 0.8, f"mod={mod}")
data.health['sick_days'] = 0

# Daily
hm.process_daily()
check("daily runs ok", True)


# === 3. Housing System ===
print("\n=== 3. Housing System ===")
data = GameData()
hh = HousingManager(data)

check("initial type=rent", data.housing['type'] == '租屋')

# Rent
data.cash = 20000
old = data.cash
hh.rent_property()
check("rent costs 16000", data.cash == old - 16000, f"cash={data.cash}")

# Can't buy same tier (try downgrade)
msg = hh.buy_property('租屋')
check("can't buy same tier", "只能升級" in msg, msg)

# Buy small apartment first (need 250k)
data.cash = 300000
msg = hh.buy_property('小套房')
check("buy small apt succeeds", data.housing['type'] != '租屋', repr(msg))
check("type=small_apt", data.housing['type'] == '小套房')

# Buy apartment
data.cash = 700000
hh.buy_property('公寓')
check("type=apartment", data.housing['type'] == '公寓')
check("property_value>0", data.housing['property_value'] > 0, f"val={data.housing['property_value']}")

# Install facility
old_c = data.housing['comfort']
data.cash = 20000
msg = hh.install_facility('冷氣')
check("install returns msg", '冷氣' in msg, msg)
check("comfort up", data.housing['comfort'] > old_c, f"com={data.housing['comfort']}")
check("facility listed", '冷氣' in data.housing['facilities'])

# Can't install twice
msg = hh.install_facility('冷氣')
check("no double install", "已安裝" in msg)

# Sell
hh.sell_property()
check("back to rent", data.housing['type'] == '租屋')

# Monthly cost
check("monthly cost > 0", hh.monthly_cost() > 0, f"cost={hh.monthly_cost()}")


# === 4. Education System ===
print("\n=== 4. Education System ===")
data = GameData()
em = EducationManager(data)

check("initial degree=high", data.education['degree'] == '高中')
check("initial job=none", data.education['job_title'] == '無業')
check("initial salary=0", data.education['base_salary'] == 0)

# Study
data.cash = 100000
em.study_degree('專科')
check("degree=college", data.education['degree'] == '專科')
check("salary=500", data.education['base_salary'] == 500)

# Can't study same
msg = em.study_degree('專科')
check("can't study same", "已有" in msg or "更高" in msg, msg)

# Study bachelor
data.cash = 300000
em.study_degree('學士')
check("degree=bachelor", data.education['degree'] == '學士')
check("salary=800", data.education['base_salary'] == 800)

# Learn skill
data.cash = 5000
em.learn_skill('程式', '基礎')
check("skill=1", data.education['skills'].get('程式', 0) == 1)

# Get cert
data.cash = 20000
em.get_certification('PMP')
check("PMP certified", 'PMP' in data.education['certifications'])
check("management skill up", data.education['skills'].get('管理', 0) > 0)

# Apply job
em.apply_job('作業員')
check("job=worker", data.education['job_title'] == '作業員')
check("salary=400", data.education['base_salary'] == 400)

# Can't get engineer (no skill)
msg = em.apply_job('工程師')
check("engineer blocked", "不足" in msg, msg)

# Quit
em.quit_job()
check("job=none after quit", data.education['job_title'] == '無業')

# Daily salary
data.education['job_title'] = '作業員'
data.education['base_salary'] = 400
old = data.cash
em.process_daily()
check("salary deposited", data.cash > old, f"cash={data.cash}")

# Available jobs
jobs = em.available_jobs()
check("jobs is list", isinstance(jobs, list))
check("has jobs", len(jobs) > 0, f"count={len(jobs)}")


# === 5. Social System ===
print("\n=== 5. Social System ===")
data = GameData()
sm = SocialManager(data)

check("initial rep=10", data.social['reputation'] == 10)

# Attend event
data.cash = 10000
data.health['energy'] = 100
old_rep = data.social['reputation']
old_cash = data.cash
sm.attend_event('商業聚會')
check("rep up", data.social['reputation'] > old_rep, f"rep={data.social['reputation']}")
check("cash deducted", data.cash < old_cash, f"cash={data.cash}")
check("network up", data.social['network_size'] > 0)
check("events_attended up", data.social['events_attended'] > 0)

# Network
data.health['energy'] = 100
old_rep2 = data.social['reputation']
old_rels = len(data.social['relationships'])
sm.network()
check("network ok", data.social['reputation'] > old_rep2 or len(data.social['relationships']) > old_rels)

# Give gift
if data.social['relationships']:
    target = data.social['relationships'][0]['name']
    old_close = data.social['relationships'][0]['closeness']
    data.cash = 5000
    sm.give_gift(target)
    check("gift closeness up", data.social['relationships'][0]['closeness'] > old_close)

# No cash gift
data.cash = 0
msg = sm.give_gift()
check("gift fails no cash", "不足" in msg)

# Influence
data.social['reputation'] = 60
mod = sm.influence_modifier()
check("high rep mod > 1", mod > 1.0, f"mod={mod}")

data.social['reputation'] = 5
mod = sm.influence_modifier()
check("low rep mod=1", mod == 1.0, f"mod={mod}")


# === 6. Cross-System ===
print("\n=== 6. Cross-System Integration ===")
data = GameData()
hm = HealthManager(data)
hh = HousingManager(data)
em = EducationManager(data)
sm = SocialManager(data)

# Full lifecycle
data.education['job_title'] = '工程師'
data.education['base_salary'] = 1000
old = data.cash
hm.process_daily()
hh.process_daily()
em.process_daily()
sm.process_daily()
check("salary earned in daily", data.cash > old, f"{old}->{data.cash}")

# Health affects work
data.health['stress'] = 90
data.health['energy'] = 10
mod = hm.efficiency_modifier()
check("bad health low eff", mod < 0.8, f"mod={mod}")

# Housing comfort bonus
data.housing['type'] = '豪宅'
data.housing['comfort'] = 95
check("good housing bonus", hh.comfort_bonus() > 1.0)

# Education unlocks jobs
data.education['degree'] = '碩士'
data.education['skills'] = {'程式': 5, '管理': 3}
jobs = em.available_jobs()
titles = [j.split(' (')[0] for j in jobs]
check("advanced jobs avail", '技術主管' in titles or 'CTO' in titles, f"titles={titles}")

# Social rep boost
data.social['reputation'] = 80
mod = sm.influence_modifier()
check("high social boost", mod > 1.1, f"mod={mod}")


# === 7. Stress/Recovery ===
print("\n=== 7. Stress & Recovery ===")
data = GameData()
hm = HealthManager(data)

for _ in range(10):
    data.health['stress'] = min(100, data.health['stress'] + 10)
check("stress maxed", data.health['stress'] >= 100)
hm.meditate()
check("meditation reduces", data.health['stress'] < 100)

data.health['energy'] = 5
mod = hm.efficiency_modifier()
check("exhaustion penalty", mod < 0.8, f"mod={mod}")
hm.rest()
check("rest recovers", data.health['energy'] > 5)


# === Summary ===
print(f"\n{'='*50}")
print(f"Results: {PASS} passed, {FAIL} failed")
if FAIL > 0:
    print("SOME TESTS FAILED!")
    sys.exit(1)
else:
    print("ALL TESTS PASSED!")
    sys.exit(0)
