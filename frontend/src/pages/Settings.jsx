import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { prefs } from "../utils/prefs";
import PageHeader from "../components/ui/PageHeader";

export default function Settings() {
  const { user } = useAuth();
  const [density, setDensity] = useState(prefs.getDensity());
  const [lang, setLang] = useState(prefs.getLang());

  function changeDensity(value) {
    setDensity(value);
    prefs.setDensity(value);
  }
  function changeLang(value) {
    setLang(value);
    prefs.setLang(value);
  }

  return (
    <div>
      <PageHeader title="Settings" subtitle="Personalize your workspace." icon="bi-gear" />

      <div className="row g-3">
        <div className="col-12 col-lg-7">
          <div className="app-card p-4 mb-3">
            <h6 className="fw-bold mb-3"><i className="bi bi-sliders me-2 text-brand" />Appearance</h6>
            <div className="mb-3">
              <label className="form-label">Table density</label>
              <div className="btn-group d-flex" style={{ maxWidth: 320 }}>
                <button className={`btn ${density === "comfortable" ? "btn-primary" : "btn-outline-primary"}`} onClick={() => changeDensity("comfortable")}>Comfortable</button>
                <button className={`btn ${density === "compact" ? "btn-primary" : "btn-outline-primary"}`} onClick={() => changeDensity("compact")}>Compact</button>
              </div>
              <div className="form-hint">Compact reduces row spacing to fit more on screen.</div>
            </div>
            <div>
              <label className="form-label">Preferred language</label>
              <select className="form-select" style={{ maxWidth: 320 }} value={lang} onChange={(e) => changeLang(e.target.value)}>
                <option value="en">English</option>
                <option value="ml">മലയാളം (Malayalam)</option>
              </select>
              <div className="form-hint">Stored for future bilingual screens (English / Malayalam).</div>
            </div>
          </div>

          <div className="app-card p-4">
            <h6 className="fw-bold mb-3"><i className="bi bi-shield-lock me-2 text-brand" />Security</h6>
            <p className="muted mb-2">Manage your password from your profile.</p>
            <Link to="/profile" className="btn btn-outline-primary"><i className="bi bi-key me-2" />Change password</Link>
          </div>
        </div>

        <div className="col-12 col-lg-5">
          <div className="app-card p-4">
            <h6 className="fw-bold mb-3"><i className="bi bi-info-circle me-2 text-brand" />About</h6>
            <div className="detail-meta" style={{ gridTemplateColumns: "1fr" }}>
              <div><div className="dm-label">Application</div><div className="dm-value">Bye-law Management System</div></div>
              <div><div className="dm-label">Version</div><div className="dm-value">1.0.0</div></div>
              <div><div className="dm-label">Organisation</div><div className="dm-value">C-DIT, Government of Kerala</div></div>
              <div><div className="dm-label">Signed in as</div><div className="dm-value">{user?.full_name} ({user?.role_name})</div></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
