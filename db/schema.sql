-- second-plant: the context layer (plant model, tags, mappings), incidents, and an append-only decision log.
CREATE TABLE IF NOT EXISTS plants (id text PRIMARY KEY, name text NOT NULL);

-- Plant A's model: what each signal is and which process unit it belongs to.
CREATE TABLE IF NOT EXISTS signals (
  plant_id text REFERENCES plants(id), id text, name text NOT NULL, unit text, area text NOT NULL,
  sampled boolean NOT NULL DEFAULT false, normal_mean double precision, normal_std double precision,
  PRIMARY KEY (plant_id, id));

-- Plant B's tag list as it was handed over.
CREATE TABLE IF NOT EXISTS plant_tags (
  plant_id text REFERENCES plants(id), tag text, description text, unit_label text, PRIMARY KEY (plant_id, tag));

-- One row per plant B tag: what the model proposed, what the data checks say, and what a person decided.
CREATE TABLE IF NOT EXISTS mappings (
  plant_id text, tag text, proposed_signal text, proposed_conversion text, confidence double precision,
  status text NOT NULL, suggested_signal text, suggested_conversion text, reason text NOT NULL, note text,
  decision text, final_signal text, final_conversion text, decided_by text, decision_reason text, decided_at timestamptz,
  PRIMARY KEY (plant_id, tag), FOREIGN KEY (plant_id, tag) REFERENCES plant_tags(plant_id, tag));

-- Deviations at plant A with their evidence and the agent's checked note.
CREATE TABLE IF NOT EXISTS incidents (
  id text PRIMARY KEY, plant_id text REFERENCES plants(id), fault integer, evidence jsonb NOT NULL, note jsonb,
  series jsonb, state text NOT NULL DEFAULT 'open', decision text, decided_by text, decision_reason text);

-- Append-only. Each entry's hash covers the previous hash, so editing any old entry breaks the chain.
CREATE TABLE IF NOT EXISTS decision_log (
  seq bigserial PRIMARY KEY, at text NOT NULL, actor text NOT NULL, kind text NOT NULL, subject text NOT NULL,
  decision text NOT NULL, reason text NOT NULL, payload jsonb NOT NULL, prev_hash text NOT NULL, hash text NOT NULL UNIQUE);
CREATE OR REPLACE FUNCTION no_update() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'decision_log is append-only'; END $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS decision_log_append_only ON decision_log;
CREATE TRIGGER decision_log_append_only BEFORE UPDATE OR DELETE ON decision_log FOR EACH ROW EXECUTE FUNCTION no_update();
