CREATE OR REPLACE FUNCTION public.task_update()
    RETURNS TRIGGER AS $$
DECLARE
BEGIN
    PERFORM pg_notify('task_update', row_to_json(NEW)::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER task_updated
    AFTER INSERT ON tasks
    FOR EACH ROW
EXECUTE PROCEDURE public.task_update();



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
    public.facts for each row execute procedure calculate_certainty();
