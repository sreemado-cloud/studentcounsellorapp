# Student Counsellor Web Application

A comprehensive multi-tenant student counselling platform with enterprise-grade security and data isolation. Built with React, FastAPI, and MongoDB, deployable on AWS EKS with support for both on-premise and SaaS deployments.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AWS EKS Cluster                                   │
│                                                                             │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────────────────────┐ │
│  │   Frontend   │─────▶│   Backend    │─────▶│      MongoDB            │ │
│  │   (React)    │      │  (FastAPI)   │      │   Multi-Tenant DB       │ │
│  │   Nginx      │      │   Python     │      │   - Row-Level (Low)     │ │
│  │              │      │              │      │   - DB-Per-Tenant (High) │ │
│  └──────────────┘      └──────────────┘      └─────────────────────────┘ │
│         │                      │                        │                   │
│         │                      │                        │                   │
│         │         ┌────────────┴────────────┐          │                   │
│         │         │  Tenant Isolation       │          │                   │
│         │         │  Middleware Layer        │          │                   │
│         │         │  - JWT Validation       │          │                   │
│         │         │  - Institution Context  │          │                   │
│         │         │  - Role-Based Access    │          │                   │
│         │         └─────────────────────────┘          │                   │
│         │                                               │                   │
│  ┌──────┴──────┐                                        │                   │
│  │ AWS ALB     │                                        │                   │
│  │ Ingress     │                                        │                   │
│  └─────────────┘                                        │                   │
└─────────────────────────────────────────────────────────────────────────────┘

Tenant Isolation Layers:
1. Middleware: Extracts institution_id from JWT, sets tenant context
2. API Layer: Validates access based on role and institution
3. Database Layer: Applies tenant filters based on isolation strategy
```

## Features

### Core Functionality
- **Multi-Tenant Architecture**: Each university is a tenant with complete data isolation
- **Role-Based Access Control**: Students, Counsellors, and Admins with distinct permissions
- **Student-Counsellor Assignment**: Admins can assign students to counsellors (max 10 students per counsellor)
- **Secure Messaging**: Private messaging between students and their assigned counsellors
- **Conversation History**: Full conversation history preserved when students are re-assigned, with previous counsellor names masked for privacy
- **Appointments**: Book and manage counselling sessions
- **Notes**: Private note-taking for students
- **Modern UI**: Clean, responsive interface with Tailwind CSS

### Security & Isolation
- **Tenant Isolation**: Strong multi-tenant isolation at middleware and database layers
- **Data Privacy**: Students cannot see other students' data; counsellors only see their assigned students
- **JWT Authentication**: Secure token-based authentication with configurable expiration
- **Audit Logging**: Comprehensive audit trail for all administrative actions
- **Password Security**: Bcrypt hashing with password reset functionality

### Deployment Modes
- **On-Premise Mode**: Single-tenant deployment with collection-per-tenant isolation
- **SaaS Mode - Low Isolation**: Shared database with row-level filtering (cost-effective)
- **SaaS Mode - High Isolation**: Separate database per tenant (maximum security)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| Backend | FastAPI, Python 3.12, Pydantic |
| Database | MongoDB 7.0 |
| Container | Docker, Docker Compose |
| Orchestration | Kubernetes (EKS) |
| Load Balancer | AWS ALB |

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- MongoDB (or Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Using Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## API Endpoints

### Authentication
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/auth/register` | Register new user | Public |
| POST | `/api/auth/login` | Login user | Public |
| GET | `/api/auth/me` | Get current user | Authenticated |
| POST | `/api/auth/forgot-password` | Request password reset | Public |
| POST | `/api/auth/reset-password` | Reset password with token | Public |

### Admin Endpoints
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/admin/users` | Create new user (student/counsellor/admin) | Admin |
| PUT | `/api/admin/users/{id}/assign-counsellor` | Assign/reassign student to counsellor | Admin |
| PUT | `/api/admin/users/{id}/status` | Activate/deactivate user | Admin |
| PUT | `/api/admin/users/{id}/approve` | Approve pending student | Admin |
| PUT | `/api/admin/users/{id}/reject` | Reject pending student | Admin |

### User Management
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/users/counsellors` | List counsellors in institution | Authenticated |
| GET | `/api/users/{id}` | Get user details | Authenticated |
| PUT | `/api/users/me` | Update own profile | Authenticated |

### Messaging
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/messages/` | Send message | Authenticated |
| GET | `/api/messages/` | List messages (filtered by role) | Authenticated |
| GET | `/api/messages/conversations` | Get conversation summaries | Authenticated |
| PUT | `/api/messages/{id}/read` | Mark message as read | Authenticated |

### Appointments & Notes
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/appointments/` | Create appointment | Authenticated |
| GET | `/api/appointments/` | List appointments (filtered by role) | Authenticated |
| POST | `/api/notes/` | Create note | Student |
| GET | `/api/notes/` | List notes | Student |

## Deployment Options

### Quick Testing & Friend Review

For deploying so a friend can test the app, see:

- **📘 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Comprehensive guide with 8+ deployment options
- **⚡ [QUICK_DEPLOY_RAILWAY.md](QUICK_DEPLOY_RAILWAY.md)** - Step-by-step Railway.app deployment (~15 min)
- **✅ [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Pre-deployment checklist
- **👋 [FRIEND_INSTRUCTIONS.md](FRIEND_INSTRUCTIONS.md)** - Copy-paste instructions to send your friend (no tech work for them)

**Recommended for testing:** Railway.app (free tier, easy setup, ~15 minutes)

**Quick options:**
- **ngrok** - Share local instance instantly (free, 2 min)
- **Railway.app** - Easy cloud deployment (free tier, 15 min) ⭐ **RECOMMENDED**
- **Render.com** - Free tier with persistent URLs (20 min)
- **Fly.io** - Global edge deployment (25 min)

See `DEPLOYMENT_GUIDE.md` for details on all options.

---

## Production Deployment

### AWS EKS Deployment

**Recommended:** Use **Terraform** for infrastructure-as-code deployment. See **[EKS_TERRAFORM_DEPLOYMENT.md](EKS_TERRAFORM_DEPLOYMENT.md)** for complete Terraform-based setup.

**Multi-Tenant Logging:** All tenant logs are in the same log stream, but each entry includes `institution_id` for filtering. See **[EKS_LOGGING_MULTI_TENANT.md](EKS_LOGGING_MULTI_TENANT.md)** for log separation strategies.

**Alternative:** Manual setup with `eksctl` (below).

#### Prerequisites

- AWS CLI configured
- kubectl installed
- eksctl installed (or Terraform >= 1.5.0)
- AWS ECR repositories created

### 1. Create EKS Cluster

```bash
eksctl create cluster \
  --name student-counsellor \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed
```

### 2. Install AWS Load Balancer Controller

```bash
# Install AWS Load Balancer Controller
eksctl create iamserviceaccount \
  --cluster=student-counsellor \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess \
  --override-existing-serviceaccounts \
  --approve

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=student-counsellor \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

### 3. Build and Push Docker Images

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push backend
docker build -t student-counsellor-backend ./backend
docker tag student-counsellor-backend:latest $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/student-counsellor-backend:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/student-counsellor-backend:latest

# Build and push frontend
docker build -t student-counsellor-frontend ./frontend
docker tag student-counsellor-frontend:latest $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/student-counsellor-frontend:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/student-counsellor-frontend:latest
```

### 4. Deploy to EKS

```bash
# Update image references in k8s manifests
export AWS_ACCOUNT_ID=your-account-id
export AWS_REGION=us-east-1

# Apply manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/mongodb.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/network-policy.yaml
```

### 5. Verify Deployment

```bash
kubectl get pods -n student-counsellor
kubectl get services -n student-counsellor
kubectl get ingress -n student-counsellor
```

## Multi-Tenancy Implementation

The application implements comprehensive multi-tenant isolation with multiple strategies:

### Tenant Isolation Strategies

1. **Row-Level Strategy** (SaaS Low-Isolation)
   - All tenants share the same database and collections
   - Isolation achieved through `institution_id` filtering
   - Cost-effective for SaaS deployments
   - Best for: Universities willing to share infrastructure

2. **Collection-Per-Tenant Strategy** (On-Premise)
   - Each institution has separate collections (e.g., `inst_abc123_messages`)
   - Stronger isolation at the collection level
   - Best for: On-premise single-tenant deployments

3. **Database-Per-Tenant Strategy** (SaaS High-Isolation)
   - Each institution has a completely separate database
   - Maximum isolation and security
   - Best for: Universities requiring maximum data separation

### Access Control Rules

- **Students**: Can only access their own data (messages, appointments, notes)
- **Counsellors**: Can only see messages and data from their assigned students (max 10 students)
- **Admins**: Can manage all users and data within their institution
- **Cross-Tenant Protection**: One university cannot access another university's data

### Re-Assignment with History Preservation

When a student is re-assigned to a new counsellor:
- All previous conversation history is preserved
- Previous counsellor names are masked as "Previous Counsellor" for privacy
- New counsellor can see full conversation history
- Assignment history is tracked for audit purposes

### Configuration

Set isolation level via environment variables:

```bash
# Deployment mode
DEPLOYMENT_MODE=saas  # or 'onprem'

# SaaS isolation level (only applies when DEPLOYMENT_MODE=saas)
SAAS_ISOLATION_LEVEL=low   # or 'high'

# Explicit strategy override (optional)
TENANT_STRATEGY=row_level  # or 'collection_per_tenant' or 'database_per_tenant'
```

## Security Features

### Authentication & Authorization
- **JWT Authentication**: Secure token-based authentication with configurable expiration
- **Password Security**: Bcrypt hashing with salt rounds
- **Role-Based Access Control**: Strict role-based permissions (student, counsellor, admin)
- **Password Reset**: Secure password reset flow with email tokens

### Data Protection
- **Tenant Isolation**: Multi-layer isolation (middleware + database)
- **Data Encryption**: Sensitive data encrypted at rest (MongoDB encryption)
- **Audit Logging**: All administrative actions logged with user, timestamp, and metadata
- **Input Validation**: Pydantic models for request validation

### Infrastructure Security
- **CORS Protection**: Configurable allowed origins
- **Network Policies**: Kubernetes network policies for pod-to-pod communication
- **Non-Root Containers**: Containers run as non-root users
- **Secrets Management**: Kubernetes secrets for sensitive configuration
- **Rate Limiting**: API rate limiting to prevent abuse

### Privacy Controls
- **Student Data Isolation**: Students cannot see other students' data
- **Counsellor Scope**: Counsellors only see their assigned students (max 10)
- **Name Masking**: Previous counsellor names masked in conversation history
- **Institution Boundaries**: Strict enforcement of institution-level data boundaries

## Admin Features

### User Management
- **Create Users**: Admins can create students, counsellors, and other admins
- **Student-Counsellor Assignment**: Assign students to counsellors with max 10 students per counsellor limit
- **Re-Assignment**: Reassign students to different counsellors while preserving conversation history
- **User Status**: Activate/deactivate users
- **Approval Workflow**: Approve or reject pending student registrations

### Assignment Rules
- **Max Capacity**: Each counsellor can have a maximum of 10 assigned students
- **Validation**: System prevents assignment if counsellor is at capacity
- **History Preservation**: When re-assigning, all previous conversations are preserved
- **Privacy**: Previous counsellor names are masked as "Previous Counsellor" in conversation history

### Dashboard
- **User Statistics**: View counts of admins, counsellors, and students
- **Pending Approvals**: See and manage pending student registrations
- **Search & Filter**: Search users by name/email and filter by role
- **Assignment Management**: View and manage student-counsellor assignments

## Project Structure

```
StudentCounsellorApp/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes
│   │   │   ├── admin.py      # Admin endpoints (user management, assignments)
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── messages.py   # Messaging with tenant isolation
│   │   │   ├── users.py      # User management
│   │   │   └── ...
│   │   ├── core/             # Core functionality
│   │   │   ├── tenant.py     # Tenant context and middleware
│   │   │   ├── tenant_strategy.py  # Isolation strategies
│   │   │   ├── database.py   # Database connection with tenant support
│   │   │   ├── security.py   # JWT, password hashing
│   │   │   └── config.py     # Configuration with isolation settings
│   │   ├── models/           # Pydantic models
│   │   └── services/         # Business logic
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── contexts/         # Auth context
│   │   ├── pages/            # Page components
│   │   │   ├── AdminPanel.tsx    # Admin dashboard with assignments
│   │   │   ├── Messages.tsx      # Messaging interface
│   │   │   └── ...
│   │   ├── services/         # API service
│   │   └── types/            # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── k8s/                      # Kubernetes manifests for EKS
│   ├── backend.yaml
│   ├── frontend.yaml
│   ├── mongodb.yaml
│   └── ...
└── docker-compose.yml        # Local development
```

## License

MIT
