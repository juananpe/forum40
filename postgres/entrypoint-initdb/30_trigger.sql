
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