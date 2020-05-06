-- CREATE SEQUENCE IF NOT EXISTS annotations_id_seq;
-- CREATE SEQUENCE IF NOT EXISTS commentators_id_seq;
-- CREATE SEQUENCE IF NOT EXISTS comments_id_seq;
-- CREATE SEQUENCE IF NOT EXISTS documents_id_seq;
-- CREATE SEQUENCE IF NOT EXISTS facts_id_seq;
-- CREATE SEQUENCE IF NOT EXISTS labels_id_seq;
-- CREATE SEQUENCE IF NOT EXISTS sources_id_seq;

-- Drop table

-- DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA IF NOT EXISTS public;

-- DROP TABLE IF EXISTS public.users CASCADE;

CREATE TABLE IF NOT EXISTS public.users (
	id bigserial NOT NULL,
	external_id varchar NULL,
	"name" varchar NULL,
	"url" varchar NULL,
	"password" varchar NULL,
	"role" varchar NULL,
	CONSTRAINT users_pk PRIMARY KEY (id)
);

-- Drop table

-- DROP TABLE IF EXISTS public.labels CASCADE;

CREATE TABLE IF NOT EXISTS public.labels (
	id bigserial NOT NULL,
	"type" varchar NOT NULL,
	"name" varchar NOT NULL,
	labelgroup varchar NULL,
	description text NULL,
	"order" int2 NOT NULL DEFAULT 0,
	n_state int4 NOT NULL DEFAULT 0,
	source_id int8 NOT NULL,
	CONSTRAINT labels_pk PRIMARY KEY (id)
);

-- Drop table

-- DROP TABLE IF EXISTS public.sources CASCADE;

CREATE TABLE IF NOT EXISTS public.sources (
	id bigserial NOT NULL,
	"name" varchar NOT NULL,
	"domain" varchar NULL,
	CONSTRAINT sources_pk PRIMARY KEY (id)
);

-- Drop table

-- DROP TABLE IF EXISTS public.documents CASCADE;

CREATE TABLE IF NOT EXISTS public.documents (
	id bigserial NOT NULL,
	external_id varchar NULL,
	"url" varchar NULL,
	title varchar NULL,
	"text" text NULL,
	markup text NULL,
	"timestamp" timestamp NULL,
	metadata text NULL,
	source_id int8 NULL,
	embedding float8[] NULL,
	CONSTRAINT documents_pk PRIMARY KEY (id)
);


-- Drop table

-- DROP TABLE IF EXISTS public."comments" CASCADE;

CREATE TABLE IF NOT EXISTS public."comments" (
	id bigserial NOT NULL,
	external_id varchar NULL,
	doc_id int8 NULL,
	source_id int8 NULL,
	user_id int8 NULL,
	parent_comment_id int8 NULL,
	status varchar NULL,
	title varchar NULL,
	"text" text NULL,
	embedding float8[] NULL,
	"timestamp" timestamp NOT NULL,
	"year" int2 NULL,
	"month" int2 NULL,
	"day" int2 NULL,
	CONSTRAINT comments_pk PRIMARY KEY (id)
);


-- Drop table

-- DROP TABLE IF EXISTS public.facts CASCADE;

CREATE TABLE IF NOT EXISTS public.facts (
	comment_id int8 NOT NULL,
	label_id int8 NOT NULL,
	"label" bool NULL DEFAULT false,
	value int4 NULL,
	confidence float8 NULL DEFAULT 0,
	uncertaintyorder float8 NULL,
	CONSTRAINT facts_pk PRIMARY KEY (comment_id,label_id)
);


-- Drop table

-- DROP TABLE IF EXISTS public.annotations CASCADE;

CREATE TABLE IF NOT EXISTS public.annotations (
    id bigserial NOT NULL,
	label_id int8 NOT NULL,
	comment_id int8 NOT NULL,
	user_id varchar NOT NULL DEFAULT 'anonymous',
	"label" bool NOT NULL,
	CONSTRAINT annotations_pk PRIMARY KEY (id)
);


-- Drop table

-- DROP TABLE IF EXISTS public.tasks CASCADE;

CREATE TABLE IF NOT EXISTS public.tasks (
	id bigserial NOT NULL,
	pid int8 NOT NULL,
	"name" varchar NULL,
	message varchar NULL,
	progress float4 NULL,
	"timestamp" timestamp NULL
);

-- DROP TABLE IF EXISTS public.model CASCADE;

CREATE TABLE public.model (
	id bigserial NOT NULL,
	label_id int8 NOT NULL,
	"timestamp" timestamp NOT NULL,
	number_training_samples int8 NULL,
	CONSTRAINT model_pk PRIMARY KEY (id)
);

-- ALTER TABLE public."annotations" ALTER COLUMN id SET DEFAULT nextval('annotations_id_seq'::regclass);
-- ALTER TABLE public."users" ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass);
-- ALTER TABLE public."comments" ALTER COLUMN id SET DEFAULT nextval('comments_id_seq'::regclass);
-- ALTER TABLE public."documents" ALTER COLUMN id SET DEFAULT nextval('documents_id_seq'::regclass);
-- ALTER TABLE public."facts" ALTER COLUMN id SET DEFAULT nextval('facts_id_seq'::regclass);
-- ALTER TABLE public."labels" ALTER COLUMN id SET DEFAULT nextval('labels_id_seq'::regclass);
-- ALTER TABLE public."sources" ALTER COLUMN id SET DEFAULT nextval('sources_id_seq'::regclass);

CREATE OR REPLACE FUNCTION public.calculate_certainty()
	RETURNS trigger 
	LANGUAGE plpgsql
AS $body$
	BEGIN
		new.uncertaintyorder:=new.confidence*(1-new.confidence);
		return new;
	END;
$body$;


create trigger calculatecertainty before
insert
    or
update
    on
    public.facts for each row execute procedure calculate_certainty();--ALTER TABLE public."users" ADD CONSTRAINT users_pk PRIMARY KEY (id)
--ALTER TABLE public."labels" ADD CONSTRAINT labels_pk PRIMARY KEY (id)
--ALTER TABLE public."sources" ADD CONSTRAINT sources_pk PRIMARY KEY (id)
--ALTER TABLE public."documents" ADD CONSTRAINT documents_pk PRIMARY KEY (id)
--ALTER TABLE public."comments" ADD CONSTRAINT comments_pk PRIMARY KEY (id)
--ALTER TABLE public."facts" ADD CONSTRAINT facts_pk PRIMARY KEY (comment_id,label_id)
--ALTER TABLE public."annotations" ADD CONSTRAINT annotations_pk PRIMARY KEY (id)

CREATE INDEX IF NOT EXISTS facts_multicolumn_idx ON public.facts USING btree (comment_id,label_id,label);
CREATE INDEX IF NOT EXISTS facts_label_id_label_idx ON public.facts USING btree (label_id,label);
CREATE INDEX IF NOT EXISTS facts_label_idx ON public.facts USING btree (label);

CREATE INDEX IF NOT EXISTS comments_doc_id_idx ON public.comments USING btree (doc_id);
CREATE INDEX IF NOT EXISTS comments_ext_id_idx ON public.comments USING btree (external_id);
CREATE INDEX IF NOT EXISTS comments_source_id_idx ON public.comments USING btree (source_id);
CREATE INDEX IF NOT EXISTS comments_timestamp_idx ON public.comments USING btree ("timestamp");
CREATE INDEX IF NOT EXISTS comments_year_idx ON public.comments USING btree (year, month, day);

CREATE INDEX IF NOT EXISTS annotations_label_id_idx ON public.annotations USING btree (label_id);

CREATE INDEX IF NOT EXISTS documents_ext_id_idx ON public.documents USING btree (external_id);
