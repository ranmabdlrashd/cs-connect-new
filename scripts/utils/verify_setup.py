import os
from dotenv import load_dotenv

load_dotenv()

def test_routes():
    app_path = os.path.join('cs_connect', 'app.py')
    routes_path = os.path.join('cs_connect', 'routes', 'placement_routes.py')
    
    routes = [
        '/dashboard/placements',
        '/api/placements/active',
        '/api/placements/<int:drive_id>/apply',
        '/api/placements/my-applications',
        '/api/placements/eligibility-summary'
    ]
    
    print("Checking if placement blueprint is registered in app.py...")
    with open(app_path, 'r', encoding='utf-8') as f:
        app_content = f.read()
    if "from routes.placement_routes import placement_bp" in app_content and "app.register_blueprint(placement_bp)" in app_content:
        print("OK: placement_bp registered")
    else:
        print("FAIL: placement_bp NOT registered properly in app.py")

    print("\nChecking if routes are present in placement_routes.py...")
    with open(routes_path, 'r', encoding='utf-8') as f:
        routes_content = f.read()
    for route in routes:
        if route in routes_content:
            print(f"OK: Route {route} found")
        else:
            print(f"FAIL: Route {route} NOT found")

    print("\nChecking if templates exist...")
    templates = ['student_placement_portal.html']
    for t in templates:
        path = os.path.join('cs_connect', 'templates', t)
        if os.path.exists(path):
            print(f"OK: Template {t} exists")
        else:
            print(f"FAIL: Template {t} NOT found at {path}")

if __name__ == "__main__":
    test_routes()
