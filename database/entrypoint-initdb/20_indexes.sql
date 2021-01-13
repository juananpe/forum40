--ALTER TABLE public."users" ADD CONSTRAINT users_pk PRIMARY KEY (id)
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
