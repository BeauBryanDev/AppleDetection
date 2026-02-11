## How to Restart the Backend Server

The backend server needs to be manually restarted because uvicorn's auto-reload didn't pick up the routing changes.

### Steps:

1. **Find the terminal where uvicorn is running** (it should show logs like "POST /api/v1/...")

2. **Stop the server:**
   - Press `Ctrl + C` in that terminal

3. **Restart the server:**
   ```bash
   cd /home/beaunix/Documents/yieldEstimator
   ./apples/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Verify it's working:**
   - Go to http://localhost:8000/docs
   - You should now see a "Farming" section in the API docs
   - The endpoints should include:
     - GET /api/v1/farming/orchards
     - GET /api/v1/farming/orchard/{orchard_id}/trees
     - POST /api/v1/estimator/estimate

5. **Test the Estimator page:**
   - Go to http://localhost:5173/estimator
   - Upload an image
   - Select orchard and tree
   - Click "Procesar Imagen"
   - It should work now! ✅

### Why This Happened:

Uvicorn's `--reload` flag watches for file changes, but sometimes changes to the routing configuration (especially adding new router imports) don't trigger a reload. This is a known limitation of the auto-reload feature.

### Alternative (If you can't find the terminal):

If you can't find the running uvicorn terminal:

```bash
# Kill the existing uvicorn process
pkill -f "uvicorn app.main:app"

# Wait a moment
sleep 2

# Start it again
cd /home/beaunix/Documents/yieldEstimator
./apples/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
