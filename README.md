# Team Connect — Room Booking System

A modern, scalable **Room Booking System** built with Flask and Firebase. Team Connect enables organizations to intelligently manage conference rooms, track bookings, detect scheduling conflicts, and provide real-time availability insights.

**Module:** B9IS123 Programming for Information Systems  
**Institution:** Dublin Business School  


---

##  Features

### Core Functionality
- ** Room Management** — Create, view, and manage conference rooms with metadata
- ** Smart Booking System** — Reserve rooms with automatic conflict detection
- ** Real-time Clash Detection** — Prevents double-bookings instantly
- ** Occupancy Tracking** — Calculate room usage percentages and trends
- ** Booking Rescheduling** — Modify or cancel bookings with permission checks
- ** Availability Suggestions** — Find earliest free slots across the week
- ** Access Control** — Users can only manage their own bookings

### Technical Highlights
- ** Google OAuth 2.0** via Firebase Authentication
- ** Cloud Firestore Database** for real-time data consistency
- ** Responsive Web Interface** with Jinja2 templating
- ** Comprehensive Test Suite** with 21 unit + integration tests
- ** RESTful JSON API** for all CRUD operations
- ** Profile Pictures** stored in Google Cloud Storage
- ** User Statistics Dashboard** with activity tracking

---

##  System Requirements

- **Python:** 3.8+
- **OS:** Windows, macOS, Linux
- **Browser:** Modern browser supporting OAuth 2.0
- **Internet:** Required for Firebase and Google OAuth
- **Node.js:** Optional (for frontend tooling)

---

##  Installation & Setup

### 1. Clone Repository
```bash
git clone https://github.com/atyogesh501/team-connect-app.git
cd team-connect-app
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv env
env\Scripts\activate

# macOS/Linux
python3 -m venv env
source env/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Firebase Credentials
The application uses a service account key encoded in `main.py`. This is pre-configured for the demonstration project.

**For your own Firebase project:**
1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Generate a service account key (Settings → Service Accounts → Generate New Private Key)
3. Base64-encode the JSON key:
   ```bash
   cat service-account-key.json | base64 > encoded_key.txt
   ```
4. Replace the `gcpKey` variable in `main.py`

### 5. Set Environment Variables (Optional)
```bash
# .env file (create if using environment variables)
FLASK_ENV=development
FLASK_DEBUG=True
```

---

##  Running the Application

### Development Server
```bash
python main.py
```
The application will start at `http://localhost:8000`

### Production Deployment (Gunicorn)
```bash
gunicorn --bind 0.0.0.0:8000 main:app
```

### Access the Application
1. Navigate to `http://localhost:8000` in your browser
2. Click **Sign In** to authenticate with Google via Firebase
3. Start creating rooms and booking meetings!

---

##  Testing

### Run All Tests
```bash
python test_room_booking_system.py
```

### Verbose Output
```bash
python test_room_booking_system.py -v
```

### Test Coverage
The test suite includes **21 tests** across CRUD operations:

| Category | Tests | Coverage |
|----------|-------|----------|
| **CREATE** (C1-C7) | 7 | Room creation, duplicates, validation |
| **READ** (R1-R6) | 6 | Document retrieval, conversions |
| **UPDATE** (U1-U4) | 4 | Rescheduling, conflict handling |
| **DELETE** (D1-D4) | 4 | Cancellations, permissions |

**All tests use mocked Firestore** to ensure isolated, repeatable results.

### Expected Output
```
C1: Valid room name creates room and bumps stat. ... ok
C2: Duplicate room name returns error. ... ok
C3: Empty or whitespace name returns error. ... ok
...
Ran 21 tests in 0.842s
OK
```

---

##  Project Structure
team-connect-app/
│
├── main.py                           - Flask application & Firestore logic
├── test_room_booking_system.py       - CRUD test suite (21 tests)
├── requirements.txt                  - Python dependencies
├── README.md                          - Project documentation
├── .gitignore                         - Git ignore rules
│
├── templates/                         - Jinja2 HTML templates
│   ├── index.html                     - Home page & room list
│   ├── room.html                      - Room details & calendar
│   ├── edit_booking.html              - Edit/reschedule booking
│   ├── profile.html                   - User profile & statistics
│   └── about.html                     - System information
│
├── static/                            - Frontend assets
│   ├── css/                           - Stylesheets
│   ├── js/                            - JavaScript
│   └── images/                        - Icons & images
│
└── .git/                              

---

##  Architecture Overview

### Technology Stack
The application follows a simple four-layer architecture.

User Interface (HTML, CSS, JavaScript, jQuery)
        ↓
Flask Application (Routes, Jinja2 Templates, Google OAuth)
        ↓
Application Logic (Booking and User Management)
        ↓
Google Firestore Database

### Database Schema

**Firestore Collections:**

Database Collections

The project uses four main Firestore collections to store the application data.

1. Users
   - User ID
   - Email
   - Display name
   - Profile photo
   - Booking statistics
   - Date created

2. Rooms
   - Room name
   - Creator details
   - Date created

3. Bookings
   - Room
   - Meeting name
   - Date
   - Start time
   - End time
   - User details
   - Created and updated timestamps

4. Days
   - Room
   - Date
   - List of bookings for that day

---

##  API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page (login required) |
| POST | `/auth` | Google OAuth callback |

### Rooms
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all rooms |
| POST | `/add-room` | Create a new room |
| POST | `/delete-room/<room_id>` | Delete room (creator only) |
| GET | `/room/<room_id>` | View room details & bookings |

### Bookings
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/book-room` | Create a new booking |
| GET | `/my-bookings` | Fetch current user's bookings |
| POST | `/delete-booking/<booking_id>` | Cancel booking (owner only) |
| GET | `/edit-booking/<booking_id>` | Edit booking page |
| POST | `/update-booking/<booking_id>` | Update booking details |
| GET | `/room-bookings/<room_id>` | Get all bookings for a room |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/room-graph/<room_id>` | Timeline data for room (date-filtered) |
| GET | `/filter-by-day` | Bookings filtered by date |

### User Profile
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/profile` | User dashboard & statistics |
| POST | `/update-profile` | Update display name |
| POST | `/upload-photo` | Upload profile picture |

---

##  Security Features

### Authentication & Authorization
 **Google OAuth 2.0** — Secure identity verification  
 **User-scoped Queries** — Bookings filtered by `user_id` at database level  
 **Permission Checks** — Only owners can modify/delete their bookings  
 **Session Validation** — Firebase token verification on every request  

### Data Protection
 **Firestore Security Rules** — Enforce access control in database  
 **HTTPS Only** — All communication encrypted  
 **No Hardcoded Secrets** — Service keys securely encoded  
 **Input Validation** — All user inputs sanitized  

### Testing
 **D3 Permission Test** — Verifies users can't delete others' bookings  
 **Access Control Tests** — Room deletion only by creator  
 **Input Boundary Tests** — Empty names, invalid times rejected  

---

##  Key Functions

### Service Layer (main.py)

**Room Operations:**
```python
create_room_svc(user, room_name)          # Create new room
_find_room_by_name_or_id(value)           # Resolve room reference
```

**Booking Operations:**
```python
book_room_svc(user, room_ref, date, start_time, end_time, meeting_name)
cancel_booking_svc(user, meeting_name, date, room_ref)
reschedule_booking_svc(user, meeting_name, ..., new_date, new_start, new_end)
_find_user_booking(user, meeting_name, date, room_ref)
```

**Availability & Analytics:**
```python
check_booking_clash(room_id, date, start_time, end_time)      # Detect conflicts
calculate_occupancy(room_id, date)                             # % room usage
compute_free_slots(room_id, date)                              # Available time windows
find_earliest_free_slot(room_id)                               # Smart suggestion
get_or_create_day(room_id, date)                               # Day aggregation
```

**User Tracking:**
```python
bump_stat(user_id, field, amount)         # Increment user statistics
get_user_profile(user_id, email, name)    # Create/fetch user profile
```

---

##  Deployment

### Live Demo
**URL:** http://207.175.34.40:8000  
**Status:** Active  
**Platform:** Google Cloud Platform  

### Deploy to Google Cloud Run
```bash
# Create app.yaml
cat > app.yaml << EOF
runtime: python39
env: standard
entrypoint: gunicorn -b :$PORT main:app
EOF

# Deploy
gcloud app deploy
```

### Deploy to Heroku
```bash
heroku create team-connect-app
git push heroku main
heroku open
```

---

##  Academic Context

**Module:** B9IS123 Programming for Information Systems  
**Assessment:** CRUD System with Test Suite  
**Learning Outcomes:**
-  Design & implement CRUD operations
-  Write comprehensive unit tests with mocks
-  Integrate third-party authentication (OAuth)
-  Use cloud databases (Firestore)
-  Develop responsive web interfaces
-  Implement access control & security

---

##  Troubleshooting

### Issue: Firebase Connection Failed
**Solution:** Verify GCP credentials and network connectivity
```python
# Check credentials in main.py
print(service_account_info["project_id"])
```

### Issue: Tests Failing
**Solution:** Ensure all mocks are properly configured
```bash
python test_room_booking_system.py -v
```

### Issue: OAuth Login Not Working
**Solution:** Check Firebase authentication setup and authorized redirect URIs

### Issue: Bookings Not Appearing
**Solution:** Verify date format is YYYY-MM-DD and times are HH:MM (24h)

---

##  Development Notes

### Git Commit History
- **45+ commits** demonstrating incremental development
- Branch-based workflow for features
- Descriptive commit messages

### Code Quality
- **Consistent naming conventions** — snake_case for functions/variables
- **Docstrings** on all service functions
- **Type hints** where applicable (Python 3.8+)
- **Error handling** with user-friendly messages
- **Test coverage** for all CRUD operations

### Future Enhancements
-  Mobile app (React Native)
-  AI-powered scheduling assistant
-  Email reminders & calendar sync
-  Multi-timezone support
-  Real-time notifications (WebSocket)
-  Advanced analytics & reporting

---

## Youtube Referances used for project 
-  Python tutorials: https://youtube.com/playlist?list=PLNgoFk5SYUglQOaXSY8lAlPXmK6tQBHaw&si=SwBOlIlIzivOvmtQ
-  Google Firebase : https://youtu.be/d4leg9WwS8M?si=Ft0BLWSSlUUZnI91
- Google OAuth 2.0 : https://youtu.be/tKErrnfg9Q4?si=dyUS3G0V-CnIzV76

## Chat Referances used for project
 login landing page for signed-out visitors : https://share.gemini.google/uPn1oEnIgCu5
Firebase: https://share.gemini.google/ZdnBCoNDLCoL
service functions,HTTP route handlers : https://share.gemini.google/LHUIwXH75byT
Bookings section and form integrations : https://share.gemini.google/VlqumCD829Hf

##  Author

**Yogesh Reddy**  
MSc Information Systems with Computing  
Dublin Business School  
Student ID: 20101649  

**GitHub:** [github.com/atyogesh501](https://github.com/atyogesh501)  
**LinkedIn:** [linkedin.com/in/atyogesh501](https://linkedin.com/in/atyogesh501)
