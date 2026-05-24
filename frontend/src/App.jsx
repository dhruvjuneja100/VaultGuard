import { useState } from "react"
import axios from "axios"

// =============================================
// VAULTGUARD — Main App Component
// =============================================

const API_URL = "http://127.0.0.1:8000"

export default function App() {

  const [screen, setScreen]         = useState("login")
  const [token, setToken]           = useState(null)
  const [loginError, setLoginError] = useState(null)
  const [file, setFile]             = useState(null)
  const [results, setResults]       = useState(null)
  const [error, setError]           = useState(null)

  // ── Login Handler ──
  async function handleLogin(username, password) {
    try {
      const response = await axios.post(
        `${API_URL}/token`,
        new URLSearchParams({
          username: username,
          password: password
        })
      )
      setToken(response.data.access_token)
      setScreen("upload")
      setLoginError(null)
    } catch (err) {
      setLoginError(
        err.response?.data?.detail ||
        "Login failed. Please try again."
      )
    }
  }

  // ── File Selection Handler ──
  function handleFileChange(event) {
    const selectedFile = event.target.files[0]

    if (selectedFile && !selectedFile.name.endsWith('.pdf')) {
      setError("Please upload a PDF file only")
      setFile(null)
      return
    }

    const fileSizeKB = selectedFile.size / 1024
    if (fileSizeKB < 10) {
      setError("File too small — please upload a real bank statement")
      setFile(null)
      return
    }

   
    if (fileSizeKB < 1) {
    setError("File too small — please upload a real bank statement")
    setFile(null)
    return
}

    setFile(selectedFile)
    setError(null)
  }

  // ── Analyze Handler ──
  async function handleSubmit() {
    if (!file) {
      setError("Please select a PDF file first")
      return
    }

    setScreen("loading")
    setError(null)

    try {
      const formData = new FormData()
      formData.append("file", file)

      const response = await axios.post(
        `${API_URL}/analyze-pdf`,
        formData,
        {
          headers: {
            "Content-Type":  "multipart/form-data",
            "Authorization": `Bearer ${token}`
          }
        }
      )

      setResults(response.data)
      setScreen("results")

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Something went wrong. Please try again."
      )
      setScreen("upload")
    }
  }

  // ── Reset Handler ──
  function handleReset() {
    setFile(null)
    setResults(null)
    setError(null)
    setScreen("upload")
  }

  // ── Logout Handler ──
  function handleLogout() {
    setToken(null)
    setFile(null)
    setResults(null)
    setError(null)
    setLoginError(null)
    setScreen("login")
  }

  return (
    <div style={styles.app}>
      <Header
        isLoggedIn={token !== null}
        onLogout={handleLogout}
      />

      {screen === "login" && (
        <LoginScreen
          onLogin={handleLogin}
          error={loginError}
        />
      )}

      {screen === "upload" && (
        <UploadScreen
          file={file}
          error={error}
          onFileChange={handleFileChange}
          onSubmit={handleSubmit}
        />
      )}

      {screen === "loading" && <LoadingScreen />}

      {screen === "results" && (
        <ResultsScreen
          results={results}
          onReset={handleReset}
        />
      )}
    </div>
  )
}

// =============================================
// HEADER
// =============================================

function Header({ isLoggedIn, onLogout }) {
  return (
    <header style={styles.header}>
      <div style={styles.headerContent}>
        <div style={styles.logo}>
          🔐 VaultGuard
        </div>
        <div style={styles.headerRight}>
          <div style={styles.tagline}>
            AI-Powered Bank Statement Forensics
          </div>
          {isLoggedIn && (
            <button
              onClick={onLogout}
              style={styles.logoutButton}
            >
              Logout
            </button>
          )}
        </div>
      </div>
    </header>
  )
}

// =============================================
// LOGIN SCREEN
// =============================================

function LoginScreen({ onLogin, error }) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading]   = useState(false)

  async function handleSubmit() {
    if (!username || !password) return
    setLoading(true)
    await onLogin(username, password)
    setLoading(false)
  }

  return (
    <main style={styles.main}>
      <div style={styles.uploadCard}>

        <div style={styles.loginIcon}>🔐</div>

        <h1 style={styles.title}>
          Welcome to VaultGuard
        </h1>
        <p style={styles.subtitle}>
          Sign in to access the AI fraud detection system
        </p>

        <div style={styles.inputGroup}>
          <label style={styles.label}>Username</label>
          <input
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            style={styles.input}
            placeholder="Enter username"
          />
        </div>

        <div style={styles.inputGroup}>
          <label style={styles.label}>Password</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            style={styles.input}
            placeholder="Enter password"
            onKeyDown={e => e.key === "Enter" && handleSubmit()}
          />
        </div>

        {error && (
          <div style={styles.errorBox}>
            ⚠️ {error}
          </div>
        )}

        <button
          onClick={handleSubmit}
          style={{
            ...styles.analyzeButton,
            opacity: loading ? 0.7 : 1
          }}
          disabled={loading}
        >
          {loading ? "Signing in..." : "🔑 Sign In"}
        </button>

        <div style={styles.demoCredentials}>
          <p style={styles.demoTitle}>Demo Credentials</p>
          <p style={styles.demoText}>
            Username: <strong style={styles.demoValue}>admin</strong>
          </p>
          <p style={styles.demoText}>
            Password: <strong style={styles.demoValue}>vaultguard123</strong>
          </p>
        </div>

      </div>
    </main>
  )
}

// =============================================
// UPLOAD SCREEN
// =============================================

function UploadScreen({ file, error, onFileChange, onSubmit }) {
  return (
    <main style={styles.main}>
      <div style={styles.uploadCard}>

        <h1 style={styles.title}>
          Detect Loan Fraud Instantly
        </h1>
        <p style={styles.subtitle}>
          Upload a bank statement PDF and our AI will analyze
          it for signs of tampering and fraud in seconds.
        </p>

        <div style={styles.uploadArea}>
          <div style={styles.uploadIcon}>📄</div>
          <p style={styles.uploadText}>
            {file ? `✅ ${file.name}` : "Drop your PDF here or click to browse"}
          </p>

          <input
            type="file"
            accept=".pdf"
            onChange={onFileChange}
            style={styles.fileInput}
            id="fileInput"
          />

          <label
            htmlFor="fileInput"
            style={styles.browseButton}
          >
            Browse Files
          </label>
        </div>

        {error && (
          <div style={styles.errorBox}>
            ⚠️ {error}
          </div>
        )}

        <button
          onClick={onSubmit}
          style={{
            ...styles.analyzeButton,
            opacity: file ? 1 : 0.5,
            cursor: file ? 'pointer' : 'not-allowed'
          }}
          disabled={!file}
        >
          🔍 Analyze Statement
        </button>

        <div style={styles.features}>
          <Feature icon="🧠" text="ML Fraud Detection" />
          <Feature icon="🔍" text="PDF Forensics" />
          <Feature icon="⚡" text="Instant Results" />
        </div>

      </div>
    </main>
  )
}

function Feature({ icon, text }) {
  return (
    <div style={styles.feature}>
      <span>{icon}</span>
      <span style={styles.featureText}>{text}</span>
    </div>
  )
}

// =============================================
// LOADING SCREEN
// =============================================

function LoadingScreen() {
  return (
    <main style={styles.main}>
      <div style={styles.loadingCard}>
        <div style={styles.spinner}></div>
        <h2 style={styles.loadingTitle}>
          Analyzing Statement...
        </h2>
        <p style={styles.loadingText}>
          Running PDF forensics and ML analysis
        </p>
        <div style={styles.loadingSteps}>
          <p>🔍 Extracting transactions...</p>
          <p>📊 Analyzing patterns...</p>
          <p>🧠 Running ML model...</p>
          <p>🔐 Checking PDF integrity...</p>
        </div>
      </div>
    </main>
  )
}

// =============================================
// RESULTS SCREEN
// =============================================

function ResultsScreen({ results, onReset }) {

  const scoreColor =
    results.risk_score >= 70 ? "#ef4444" :
    results.risk_score >= 40 ? "#f59e0b" :
                               "#22c55e"

  const verdictBg =
    results.verdict === "HIGH RISK"   ? "#450a0a" :
    results.verdict === "MEDIUM RISK" ? "#451a03" :
                                        "#052e16"

  return (
    <main style={styles.main}>
      <div style={styles.resultsCard}>

        <h2 style={styles.resultsTitle}>
          Analysis Complete
        </h2>
        <p style={styles.filename}>
          📄 {results.filename}
        </p>

        <div style={styles.scoreContainer}>
          <div style={{
            ...styles.scoreCircle,
            borderColor: scoreColor,
            boxShadow: `0 0 30px ${scoreColor}40`
          }}>
            <div style={{
              ...styles.scoreNumber,
              color: scoreColor
            }}>
              {results.risk_score}
            </div>
            <div style={styles.scoreLabel}>
              Risk Score
            </div>
          </div>
        </div>

        <div style={{
          ...styles.verdictBadge,
          backgroundColor: verdictBg,
          borderColor: scoreColor,
          color: scoreColor
        }}>
          {results.verdict === "HIGH RISK"   ? "🔴" :
           results.verdict === "MEDIUM RISK" ? "🟡" : "🟢"}
          {" "}{results.verdict}
        </div>

        <div style={styles.statsRow}>
          <Stat label="ML Score"     value={`${results.ml_score}/100`} />
          <Stat label="Forensics"    value={`${results.forensics_score}/75`} />
          <Stat label="Confidence"   value={`${results.confidence}%`} />
          <Stat label="Transactions" value={results.transactions_found} />
        </div>

        {results.flags.length > 0 ? (
          <div style={styles.flagsSection}>
            <h3 style={styles.flagsTitle}>
              ⚠️ Fraud Signals Detected
            </h3>
            {results.flags.map((flag, index) => (
              <div key={index} style={styles.flagItem}>
                🚩 {flag}
              </div>
            ))}
          </div>
        ) : (
          <div style={styles.cleanSection}>
            ✅ No fraud signals detected
          </div>
        )}

        <div style={styles.fontsSection}>
          <p style={styles.fontsText}>
            Fonts detected: {results.fonts_detected.join(", ")}
          </p>
        </div>

        <button onClick={onReset} style={styles.resetButton}>
          🔄 Analyze Another Statement
        </button>

      </div>
    </main>
  )
}

function Stat({ label, value }) {
  return (
    <div style={styles.stat}>
      <div style={styles.statValue}>{value}</div>
      <div style={styles.statLabel}>{label}</div>
    </div>
  )
}

// =============================================
// STYLES
// =============================================

const styles = {
  app: {
    minHeight: "100vh",
    backgroundColor: "#0f172a",
  },

  // Header
  header: {
    backgroundColor: "#1e293b",
    borderBottom: "1px solid #334155",
    padding: "16px 24px",
  },
  headerContent: {
    maxWidth: "800px",
    margin: "0 auto",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  headerRight: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
  },
  logo: {
    fontSize: "22px",
    fontWeight: "700",
    color: "#f1f5f9",
  },
  tagline: {
    fontSize: "13px",
    color: "#94a3b8",
  },
  logoutButton: {
    backgroundColor: "transparent",
    border: "1px solid #334155",
    color: "#94a3b8",
    padding: "6px 14px",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "13px",
  },

  // Main layout
  main: {
    maxWidth: "600px",
    margin: "40px auto",
    padding: "0 20px",
  },

  // Cards
  uploadCard: {
    backgroundColor: "#1e293b",
    borderRadius: "16px",
    padding: "40px",
    border: "1px solid #334155",
  },

  // Login
  loginIcon: {
    fontSize: "48px",
    textAlign: "center",
    marginBottom: "16px",
  },
  inputGroup: {
    marginBottom: "16px",
  },
  label: {
    display: "block",
    color: "#94a3b8",
    fontSize: "13px",
    marginBottom: "6px",
    fontWeight: "600",
  },
  input: {
    width: "100%",
    padding: "12px 16px",
    backgroundColor: "#0f172a",
    border: "1px solid #334155",
    borderRadius: "8px",
    color: "#f1f5f9",
    fontSize: "14px",
    outline: "none",
    boxSizing: "border-box",
  },
  demoCredentials: {
    marginTop: "24px",
    padding: "16px",
    backgroundColor: "#0f172a",
    borderRadius: "8px",
    border: "1px solid #334155",
    textAlign: "center",
  },
  demoTitle: {
    color: "#64748b",
    fontSize: "12px",
    fontWeight: "600",
    marginBottom: "8px",
    textTransform: "uppercase",
    letterSpacing: "1px",
  },
  demoText: {
    color: "#64748b",
    fontSize: "13px",
    marginBottom: "4px",
  },
  demoValue: {
    color: "#94a3b8",
  },

  // Title
  title: {
    fontSize: "26px",
    fontWeight: "700",
    color: "#f1f5f9",
    marginBottom: "12px",
    textAlign: "center",
  },
  subtitle: {
    fontSize: "14px",
    color: "#94a3b8",
    textAlign: "center",
    marginBottom: "32px",
    lineHeight: "1.6",
  },

  // Upload
  uploadArea: {
    border: "2px dashed #334155",
    borderRadius: "12px",
    padding: "32px",
    textAlign: "center",
    marginBottom: "24px",
    backgroundColor: "#0f172a",
  },
  uploadIcon: {
    fontSize: "48px",
    marginBottom: "12px",
  },
  uploadText: {
    color: "#94a3b8",
    marginBottom: "16px",
    fontSize: "14px",
  },
  fileInput: {
    display: "none",
  },
  browseButton: {
    backgroundColor: "#3b82f6",
    color: "white",
    padding: "10px 24px",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "600",
    display: "inline-block",
  },

  // Buttons
  analyzeButton: {
    width: "100%",
    padding: "14px",
    backgroundColor: "#3b82f6",
    color: "white",
    border: "none",
    borderRadius: "10px",
    fontSize: "16px",
    fontWeight: "600",
    cursor: "pointer",
    marginBottom: "24px",
  },
  resetButton: {
    width: "100%",
    padding: "14px",
    backgroundColor: "#1e293b",
    color: "#94a3b8",
    border: "1px solid #334155",
    borderRadius: "10px",
    fontSize: "15px",
    fontWeight: "600",
    cursor: "pointer",
    marginTop: "16px",
  },

  // Error
  errorBox: {
    backgroundColor: "#450a0a",
    border: "1px solid #ef4444",
    color: "#fca5a5",
    padding: "12px 16px",
    borderRadius: "8px",
    marginBottom: "16px",
    fontSize: "14px",
  },

  // Features
  features: {
    display: "flex",
    justifyContent: "center",
    gap: "24px",
  },
  feature: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  featureText: {
    fontSize: "13px",
    color: "#64748b",
  },

  // Loading
  loadingCard: {
    backgroundColor: "#1e293b",
    borderRadius: "16px",
    padding: "60px 40px",
    border: "1px solid #334155",
    textAlign: "center",
  },
  spinner: {
    width: "48px",
    height: "48px",
    border: "4px solid #334155",
    borderTop: "4px solid #3b82f6",
    borderRadius: "50%",
    margin: "0 auto 24px",
    animation: "spin 1s linear infinite",
  },
  loadingTitle: {
    fontSize: "22px",
    fontWeight: "700",
    color: "#f1f5f9",
    marginBottom: "8px",
  },
  loadingText: {
    color: "#94a3b8",
    marginBottom: "24px",
  },
  loadingSteps: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    color: "#64748b",
    fontSize: "14px",
  },

  // Results
  resultsCard: {
    backgroundColor: "#1e293b",
    borderRadius: "16px",
    padding: "40px",
    border: "1px solid #334155",
  },
  resultsTitle: {
    fontSize: "22px",
    fontWeight: "700",
    color: "#f1f5f9",
    textAlign: "center",
    marginBottom: "4px",
  },
  filename: {
    color: "#64748b",
    fontSize: "13px",
    textAlign: "center",
    marginBottom: "32px",
  },
  scoreContainer: {
    display: "flex",
    justifyContent: "center",
    marginBottom: "24px",
  },
  scoreCircle: {
    width: "140px",
    height: "140px",
    borderRadius: "50%",
    border: "6px solid",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#0f172a",
  },
  scoreNumber: {
    fontSize: "42px",
    fontWeight: "800",
    lineHeight: "1",
  },
  scoreLabel: {
    fontSize: "12px",
    color: "#64748b",
    marginTop: "4px",
  },
  verdictBadge: {
    textAlign: "center",
    padding: "12px 24px",
    borderRadius: "10px",
    border: "1px solid",
    fontSize: "18px",
    fontWeight: "700",
    marginBottom: "24px",
    letterSpacing: "1px",
  },
  statsRow: {
    display: "flex",
    justifyContent: "space-between",
    backgroundColor: "#0f172a",
    borderRadius: "12px",
    padding: "16px",
    marginBottom: "24px",
  },
  stat: {
    textAlign: "center",
    flex: 1,
  },
  statValue: {
    fontSize: "18px",
    fontWeight: "700",
    color: "#f1f5f9",
  },
  statLabel: {
    fontSize: "11px",
    color: "#64748b",
    marginTop: "4px",
  },
  flagsSection: {
    backgroundColor: "#450a0a",
    border: "1px solid #7f1d1d",
    borderRadius: "12px",
    padding: "16px",
    marginBottom: "16px",
  },
  flagsTitle: {
    color: "#fca5a5",
    fontSize: "14px",
    fontWeight: "600",
    marginBottom: "12px",
  },
  flagItem: {
    color: "#fca5a5",
    fontSize: "13px",
    padding: "6px 0",
    borderBottom: "1px solid #7f1d1d",
  },
  cleanSection: {
    backgroundColor: "#052e16",
    border: "1px solid #14532d",
    borderRadius: "12px",
    padding: "16px",
    color: "#86efac",
    fontSize: "14px",
    textAlign: "center",
    marginBottom: "16px",
  },
  fontsSection: {
    marginBottom: "8px",
  },
  fontsText: {
    color: "#64748b",
    fontSize: "12px",
    textAlign: "center",
  },
}