import { useEffect, useState } from "react";
import "./App.css";

type Job = {
  id: number;
  title: string;
  company: string;
  location: string;
  url: string;
  score: number;
  status: string;
};

type JobDetails = {
  success: boolean;
  job: {
    id: number;
    title: string;
    company: string;
    location: string;
    description: string;
    url: string;
    score: number;
    status: string;
  };
  analysis: {
    score: number;
    matched_skills: string[];
    missing_skills: string[];
    start_date: {
      target: string | null;
      detected: string | null;
      status: string;
    };
    details: {
      internship: number;
      development: number;
      location: number;
      junior: number;
      skills: number;
      fullstack_bonus: number;
      start_date_bonus: number;
    };
  };
};


type ApplicationData = {
  subject: string;
  email_body: string;
  linkedin_message: string;
  strengths: string[];
  model_used?: string;
};


type FollowUpData = {
  subject: string;
  follow_up_message: string;
  linkedin_message: string;
  model_used?: string;
};

type ApplicationHistoryItem = {
  id: number;
  job_id: number;
  company: string;
  title: string;
  location: string;
  url: string;
  score: number;
  status: string;
  subject: string;
  email_body: string;
  linkedin_message: string;
  strengths: string[];
  model_used?: string;
  created_at: string;
  updated_at: string;
  sent_at: string | null;
  follow_up_at: string | null;
};

const API =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

const statusLabels: Record<string, string> = {
  found: "À postuler",
  applied: "Postulé",
  interview: "Entretien",
  rejected: "Refusé",
  accepted: "Accepté",
};

function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);

  const [details, setDetails] =
    useState<JobDetails | null>(null);

  const [detailsLoading, setDetailsLoading] =
    useState(false);

  const [application, setApplication] =
    useState<ApplicationData | null>(null);

  const [applicationLoading, setApplicationLoading] =
    useState(false);

  const [followUp, setFollowUp] =
    useState<FollowUpData | null>(null);

  const [followUpLoading, setFollowUpLoading] =
    useState(false);

  const [activeTab, setActiveTab] =
    useState<"offers" | "applications">("offers");

  const [applications, setApplications] =
    useState<ApplicationHistoryItem[]>([]);

  const [applicationFilter, setApplicationFilter] =
    useState<"all" | "followup">("all");

  const [searchTerm, setSearchTerm] =
    useState("");

  const [statusFilter, setStatusFilter] =
    useState("all");

  const [minScore, setMinScore] =
    useState(0);

  const loadJobs = async () => {
    const response = await fetch(`${API}/jobs`);
    const data = await response.json();
    setJobs(data);
  };

  const searchJobs = async () => {
    setLoading(true);

    try {
      await fetch(`${API}/fetch-all`, {
        method: "POST",
      });

      await loadJobs();
    } catch (error) {
      console.error(error);
    }

    setLoading(false);
  };

  const updateStatus = async (
    id: number,
    status: string
  ) => {
    const response = await fetch(
      `${API}/jobs/${id}/status`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          status,
        }),
      }
    );

    const data = await response.json();

    if (data.success) {
      setJobs((currentJobs) =>
        currentJobs.map((job) =>
          job.id === id
            ? { ...job, status }
            : job
        )
      );
    }
  };

  const showDetails = async (id: number) => {
    setDetailsLoading(true);

    try {
      const response = await fetch(
        `${API}/jobs/${id}/details`
      );

      const data = await response.json();

      if (data.success) {
        setDetails(data);
      }
    } catch (error) {
      console.error(error);
    }

    setDetailsLoading(false);
  };

  const loadApplications = async () => {
    try {
      const response = await fetch(
        `${API}/applications`
      );

      const data = await response.json();

      if (data.success) {
        setApplications(data.applications);
      }
    } catch (error) {
      console.error(error);
    }
  };

  const generateFollowUp = async (jobId: number) => {
    setFollowUpLoading(true);
    setFollowUp(null);

    try {
      const response = await fetch(
        `${API}/jobs/${jobId}/generate-follow-up`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (data.success) {
        setFollowUp(data.follow_up);
      } else {
        alert(
          data.error || "Impossible de générer la relance"
        );
      }
    } catch (error) {
      console.error(error);
      alert("Erreur pendant la génération de la relance");
    } finally {
      setFollowUpLoading(false);
    }
  };

  const scheduleFollowUp = async (jobId: number) => {
    try {
      const response = await fetch(
        `${API}/jobs/${jobId}/application/follow-up`,
        {
          method: "PATCH",
        }
      );

      const data = await response.json();

      if (data.success) {
        await loadApplications();
      } else {
        alert(
          data.error || "Erreur pendant la programmation"
        );
      }
    } catch (error) {
      console.error(error);
      alert("Impossible de programmer la relance");
    }
  };

  const markAsSent = async (jobId: number) => {
    try {
      const response = await fetch(
        `${API}/jobs/${jobId}/application/sent`,
        {
          method: "PATCH",
        }
      );

      const data = await response.json();

      if (data.success) {
        await loadApplications();
        await loadJobs();
      } else {
        alert(data.error || "Erreur");
      }
    } catch (error) {
      console.error(error);
      alert("Impossible de mettre à jour la candidature");
    }
  };



  const deleteApplication = async (id: number) => {
    const confirmed = window.confirm(
      "Supprimer cette candidature sauvegardée ?"
    );

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(
        `${API}/jobs/${id}/application`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (data.success) {
        setApplication(null);
      } else {
        alert(
          data.error || "Impossible de supprimer la candidature"
        );
      }
    } catch (error) {
      console.error(error);
      alert("Erreur pendant la suppression");
    }
  };

  const prepareApplication = async (id: number) => {
    setApplicationLoading(true);

    try {
      const response = await fetch(
        `${API}/jobs/${id}/prepare-application`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error || "Erreur backend"
        );
      }

      if (data.success) {
        setApplication(data.application);
      } else {
        alert(
          data.error || "Erreur pendant la génération"
        );
      }
    } catch (error) {
      console.error(error);

      alert(
        error instanceof Error
          ? error.message
          : "Impossible de contacter l'IA"
      );
    } finally {
      setApplicationLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
    loadApplications();
  }, []);

  const filteredJobs = jobs.filter((job) => {
    const search = searchTerm.toLowerCase().trim();

    const matchesSearch =
      search === "" ||
      job.title.toLowerCase().includes(search) ||
      job.company.toLowerCase().includes(search) ||
      job.location.toLowerCase().includes(search);

    const matchesStatus =
      statusFilter === "all" ||
      job.status === statusFilter;

    const matchesScore =
      job.score >= minScore;

    return (
      matchesSearch &&
      matchesStatus &&
      matchesScore
    );
  });

  const applicationsToDisplay =
    applications.filter((item) => {
      if (applicationFilter === "all") {
        return true;
      }

      if (!item.follow_up_at) {
        return false;
      }

      const followUpDate =
        new Date(item.follow_up_at);

      const today = new Date();

      followUpDate.setHours(0, 0, 0, 0);
      today.setHours(0, 0, 0, 0);

      return followUpDate <= today;
    });

  const followUpCount =
    applications.filter((item) => {
      if (!item.follow_up_at) {
        return false;
      }

      const followUpDate =
        new Date(item.follow_up_at);

      const today = new Date();

      followUpDate.setHours(0, 0, 0, 0);
      today.setHours(0, 0, 0, 0);

      return followUpDate <= today;
    }).length;

  return (
    <div className="app">
      <header>
        <div>
          <h1>AI Internship Hunter</h1>
          <p>
            Recherche et suivi intelligent de mes stages
          </p>
        </div>

        <button
          className="search-button"
          onClick={searchJobs}
          disabled={loading}
        >
          {loading
            ? "Recherche en cours..."
            : "🔎 Rechercher de nouveaux stages"}
        </button>
      </header>

      <section className="stats">
        <div className="stat">
          <strong>{jobs.length}</strong>
          <span>Offres</span>
        </div>

        <div className="stat">
          <strong>
            {jobs.filter(
              (job) => job.score >= 70
            ).length}
          </strong>
          <span>Match ≥ 70%</span>
        </div>

        <div className="stat">
          <strong>
            {jobs.filter(
              (job) => job.status === "applied"
            ).length}
          </strong>
          <span>Candidatures envoyées</span>
        </div>

        <div className="stat">
          <strong>
            {jobs.filter(
              (job) => job.status === "interview"
            ).length}
          </strong>
          <span>Entretiens</span>
        </div>
      </section>

      <main>
        <div className="dashboard-tabs">
        <button
          className={
            activeTab === "offers"
              ? "tab-button active"
              : "tab-button"
          }
          onClick={() => setActiveTab("offers")}
        >
          🔎 Offres
        </button>

        <button
          className={
            activeTab === "applications"
              ? "tab-button active"
              : "tab-button"
          }
          onClick={() => {
            setActiveTab("applications");
            loadApplications();
          }}
        >
          📄 Mes candidatures
          ({applications.length})
        </button>
      </div>

      {activeTab === "offers" && (
        <>
          <div className="filters">
            <input
              type="text"
              placeholder="🔎 Rechercher un poste, entreprise ou ville..."
              value={searchTerm}
              onChange={(e) =>
                setSearchTerm(e.target.value)
              }
            />

            <select
              value={statusFilter}
              onChange={(e) =>
                setStatusFilter(e.target.value)
              }
            >
              <option value="all">
                Tous les statuts
              </option>

              <option value="found">
                À postuler
              </option>

              <option value="applied">
                Postulé
              </option>

              <option value="interview">
                Entretien
              </option>

              <option value="rejected">
                Refusé
              </option>

              <option value="accepted">
                Accepté
              </option>
            </select>

            <select
              value={minScore}
              onChange={(e) =>
                setMinScore(
                  Number(e.target.value)
                )
              }
            >
              <option value={0}>
                Tous les scores
              </option>

              <option value={50}>
                Score ≥ 50%
              </option>

              <option value={70}>
                Score ≥ 70%
              </option>

              <option value={80}>
                Score ≥ 80%
              </option>
            </select>
          </div>

          <div className="results-count">
            {filteredJobs.length} offre(s) affichée(s)
          </div>

          <h2>Stages recommandés</h2>

        <div className="jobs">
          {filteredJobs.map((job) => (
            <article
              className="job-card"
              key={job.id}
            >
              <div className="score">
                {job.score}%
              </div>

              <div className="job-content">
                <span
                  className={`status status-${job.status}`}
                >
                  {statusLabels[job.status]}
                </span>

                <h3>{job.title}</h3>
                <h4>{job.company}</h4>
                <p>📍 {job.location}</p>

                <div className="status-actions">
                  {[
                    ["found", "À postuler"],
                    ["applied", "✅ Postulé"],
                    ["interview", "💬 Entretien"],
                    ["rejected", "❌ Refusé"],
                    ["accepted", "🎉 Accepté"],
                  ].map(([status, label]) => (
                    <button
                      key={status}
                      className={
                        job.status === status
                          ? "active"
                          : ""
                      }
                      onClick={() =>
                        updateStatus(
                          job.id,
                          status
                        )
                      }
                    >
                      {label}
                    </button>
                  ))}
                </div>

                <div className="actions">
                  <button
                    className="details-button"
                    onClick={() =>
                      showDetails(job.id)
                    }
                  >
                    🔍 Voir détails
                  </button>

                  {job.url && (
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Voir l'offre ↗
                    </a>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
        </>
      )}

      {activeTab === "applications" && (
        <section className="applications-list">
          <h2>Mes candidatures</h2>

          <div className="application-filters">
            <button
              className={
                applicationFilter === "all"
                  ? "active"
                  : ""
              }
              onClick={() =>
                setApplicationFilter("all")
              }
            >
              Toutes ({applications.length})
            </button>

            <button
              className={
                applicationFilter === "followup"
                  ? "active"
                  : ""
              }
              onClick={() =>
                setApplicationFilter("followup")
              }
            >
              🔔 À relancer ({followUpCount})
            </button>
          </div>

          {applications.length === 0 ? (
            <div className="empty-applications">
              Aucune candidature sauvegardée pour le moment.
            </div>
          ) : (
            <div className="application-cards">
              {applicationsToDisplay.map((item) => (
                <article
                  className="application-card"
                  key={item.id}
                >
                  <div className="application-card-top">
                    <div>
                      <span
                        className={`status status-${item.status}`}
                      >
                        {statusLabels[item.status] || item.status}
                      </span>

                      <h3>{item.title}</h3>
                      <h4>{item.company}</h4>

                      <p>
                        📍 {item.location}
                      </p>
                    </div>

                    <div className="application-score">
                      {item.score}%
                    </div>
                  </div>

                  <div className="application-meta">
                    <span>
                      📅 Générée :{" "}
                      {new Date(
                        item.created_at
                      ).toLocaleDateString("fr-FR")}
                    </span>

                    <span>
                      {item.sent_at
                        ? `📨 Envoyée le ${new Date(
                            item.sent_at
                          ).toLocaleDateString("fr-FR")}`
                        : "📭 Pas encore envoyée"}
                    </span>
                  </div>

                  <div className="application-card-actions">
                    <button
                      onClick={() =>
                        showDetails(item.job_id)
                      }
                    >
                      📄 Voir la candidature
                    </button>

                    {!item.sent_at && (
                      <button
                        className="sent-button"
                        onClick={() =>
                          markAsSent(item.job_id)
                        }
                      >
                        ✅ Marquer comme envoyée
                      </button>
                    )}

                    {item.sent_at && !item.follow_up_at && (
                      <button
                        className="follow-up-button"
                        onClick={() =>
                          scheduleFollowUp(item.job_id)
                        }
                      >
                        📅 Relancer dans 7 jours
                      </button>
                    )}

                    {item.sent_at && (
                      <button
                        className="generate-followup-button"
                        onClick={() =>
                          generateFollowUp(item.job_id)
                        }
                        disabled={followUpLoading}
                      >
                        {followUpLoading
                          ? "✨ Génération..."
                          : "✨ Générer la relance"}
                      </button>
                    )}

                    {item.url && (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        🔗 Voir l'offre
                      </a>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}

          {followUp && (
            <div className="followup-result">
              <h3>✨ Relance générée</h3>

              <h4>Objet</h4>
              <div className="generated-box">
                {followUp.subject}
              </div>

              <h4>Email de relance</h4>
              <div className="generated-box email-body">
                {followUp.follow_up_message}
              </div>

              <button
                className="copy-button"
                onClick={() =>
                  navigator.clipboard.writeText(
                    followUp.follow_up_message
                  )
                }
              >
                📋 Copier l'email
              </button>

              <h4>Message LinkedIn</h4>
              <div className="generated-box">
                {followUp.linkedin_message}
              </div>

              <button
                className="copy-button"
                onClick={() =>
                  navigator.clipboard.writeText(
                    followUp.linkedin_message
                  )
                }
              >
                📋 Copier LinkedIn
              </button>

              {followUp.model_used && (
                <p className="model-used">
                  Généré avec {followUp.model_used}
                </p>
              )}
            </div>
          )}
        </section>
      )}
      </main>

      {detailsLoading && (
        <div className="loading-details">
          Analyse de l'offre...
        </div>
      )}

      {details && (
        <div
          className="modal-overlay"
          onClick={() => setDetails(null)}
        >
          <div
            className="modal"
            onClick={(e) =>
              e.stopPropagation()
            }
          >
            <button
              className="close"
              onClick={() =>
                setDetails(null)
              }
            >
              ×
            </button>

            <div className="modal-score">
              {details.analysis.score}%
            </div>

            <h2>
              {details.job.title}
            </h2>

            <h3>
              {details.job.company}
            </h3>

            <p>
              📍 {details.job.location}
            </p>

            <hr />

            <h3>Analyse du match</h3>

            <div className="analysis-grid">
              <div>
                <strong>
                  🎯 Stage
                </strong>
                <span>
                  {
                    details.analysis.details
                      .internship
                  } pts
                </span>
              </div>

              <div>
                <strong>
                  💻 Développement
                </strong>
                <span>
                  {
                    details.analysis.details
                      .development
                  } pts
                </span>
              </div>

              <div>
                <strong>
                  📍 Localisation
                </strong>
                <span>
                  {
                    details.analysis.details
                      .location
                  } pts
                </span>
              </div>

              <div>
                <strong>
                  👨‍🎓 Junior
                </strong>
                <span>
                  {
                    details.analysis.details
                      .junior
                  } pts
                </span>
              </div>

              <div>
                <strong>
                  🛠 Compétences
                </strong>
                <span>
                  {
                    details.analysis.details
                      .skills
                  } pts
                </span>
              </div>

              <div>
                <strong>
                  📅 Date
                </strong>
                <span>
                  {
                    details.analysis
                      .start_date.status
                  }
                </span>
              </div>
            </div>

            <h3>Compétences détectées</h3>

            <div className="skills">
              {details.analysis.matched_skills
                .length > 0 ? (
                details.analysis.matched_skills.map(
                  (skill) => (
                    <span
                      className="skill matched"
                      key={skill}
                    >
                      ✓ {skill}
                    </span>
                  )
                )
              ) : (
                <p>
                  Aucune compétence exacte
                  détectée.
                </p>
              )}
            </div>

            <h3>Compétences manquantes</h3>

            <div className="skills">
              {details.analysis.missing_skills.map(
                (skill) => (
                  <span
                    className="skill missing"
                    key={skill}
                  >
                    {skill}
                  </span>
                )
              )}
            </div>

            <h3>Description</h3>

            <p className="description">
              {details.job.description ||
                "Description non disponible."}
            </p>

            <button
              className="prepare-button"
              onClick={() =>
                prepareApplication(details.job.id)
              }
              disabled={applicationLoading}
            >
              {applicationLoading
                ? "✨ Gemini prépare la candidature..."
                : application
                ? "🔄 Régénérer la candidature"
                : "✨ Préparer ma candidature"}
            </button>

            {application && (
              <div className="application-result">

                <div className="application-header">
                  <span className="saved-badge">
                    📄 Candidature sauvegardée
                  </span>

                  <div className="application-actions">
                    <button
                      className="regenerate-button"
                      onClick={() =>
                        prepareApplication(details.job.id)
                      }
                      disabled={applicationLoading}
                    >
                      🔄 Régénérer
                    </button>

                    <button
                      className="delete-button"
                      onClick={() =>
                        deleteApplication(details.job.id)
                      }
                    >
                      🗑️ Supprimer
                    </button>
                  </div>
                </div>
                <h3>✨ Candidature préparée</h3>

                <h4>Objet</h4>
                <div className="generated-box">
                  {application.subject}
                </div>

                <h4>Email</h4>
                <div className="generated-box email-body">
                  {application.email_body}
                </div>

                <button
                  className="copy-button"
                  onClick={() =>
                    navigator.clipboard.writeText(
                      application.email_body
                    )
                  }
                >
                  📋 Copier l'email
                </button>

                <h4>Message LinkedIn</h4>
                <div className="generated-box">
                  {application.linkedin_message}
                </div>

                <button
                  className="copy-button"
                  onClick={() =>
                    navigator.clipboard.writeText(
                      application.linkedin_message
                    )
                  }
                >
                  📋 Copier le message LinkedIn
                </button>

                <h4>Points forts</h4>

                <ul className="strengths-list">
                  {application.strengths.map(
                    (strength, index) => (
                      <li key={index}>
                        {strength}
                      </li>
                    )
                  )}
                </ul>

                {application.model_used && (
                  <p className="model-used">
                    Généré avec {application.model_used}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
