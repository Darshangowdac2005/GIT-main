# Testing Steps for Back2U Project

## Backend API Critical-Path Testing

1. Start the backend server:
   ```
   cd backend
   venv\\Scripts\\activate    # Or source venv/bin/activate on macOS/Linux
   python server.py
   ```
2. In a new terminal, test the root endpoint:
   ```
   curl http://localhost:5000/
   ```
   Expected response:
   ```json
   {"message":"Back2U Flask API is running!"}
   ```

## Frontend Critical Testing

1. Ensure backend server is running (step above).
2. Start frontend app:
   ```
   cd frontend
   venv\\Scripts\\activate    # Or source venv/bin/activate on macOS/Linux
   python main.py
   ```
3. Confirm the app opens in your web browser displaying the main page.
4. Try navigating between pages, e.g., login, signup, report item, and admin dashboard if applicable.

---

You can extend testing later for thorough coverage of API endpoints and UI components.
