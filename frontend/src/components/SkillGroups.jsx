function Group({ title, hint, skills, tone }) {
  if (skills.length === 0) return null;

  return (
    <div className="skill-group">
      <h3 className="skill-group-title">
        {title} <span className="count">{skills.length}</span>
      </h3>
      <p className="skill-group-hint">{hint}</p>

      <ul className="chips">
        {skills.map((skill) => (
          <li key={skill}>
            <span className={`chip chip-${tone}`}>{skill}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function SkillGroups({ skillMatching }) {
  const { matched_skills, partially_matched_skills, missing_skills } = skillMatching;

  return (
    <section className="card" aria-labelledby="skills-heading">
      <h2 id="skills-heading" className="section-title">
        Skills the job asks for
      </h2>

      <div className="skill-groups">
        <Group
          title="You have"
          hint="Found in your skills list, projects or experience."
          skills={matched_skills}
          tone="have"
        />

        <Group
          title="Close"
          hint="You have something related, so each counts for half."
          skills={partially_matched_skills}
          tone="near"
        />

        <Group
          title="Missing"
          hint="Not found on your resume."
          skills={missing_skills}
          tone="miss"
        />

        {missing_skills.length === 0 && (
          <p className="prose">No required skills are missing.</p>
        )}
      </div>
    </section>
  );
}
