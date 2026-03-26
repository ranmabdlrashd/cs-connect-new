import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup module-level logger
logger = logging.getLogger(__name__)

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
    
    logger.info("Checking if placement blueprint is registered in app.py...")
    with open(app_path, 'r', encoding='utf-8') as f:
        app_content = f.read()
    if "from routes.placement_routes import placement_bp" in app_content and "app.register_blueprint(placement_bp)" in app_content:
        logger.info("OK: placement_bp registered")
    else:
        logger.error("FAIL: placement_bp NOT registered properly in app.py")

    logger.info("Checking if routes are present in placement_routes.py...")
    with open(routes_path, 'r', encoding='utf-8') as f:
        routes_content = f.read()
    for route in routes:
        if route in routes_content:
            logger.info("OK: Route %s found", route)
        else:
            logger.error("FAIL: Route %s NOT found", route)

    logger.info("Checking if templates exist...")
    templates = ['student_placement_portal.html']
    for t in templates:
        path = os.path.join('cs_connect', 'templates', t)
        if os.path.exists(path):
            logger.info("OK: Template %s exists", t)
        else:
            logger.error("FAIL: Template %s NOT found at %s", t, path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    test_routes()
