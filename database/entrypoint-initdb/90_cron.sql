SELECT cron.schedule('refresh-views', '0 */3 * * *', $$
    REFRESH MATERIALIZED VIEW public.count_comments_by_category;
    REFRESH MATERIALIZED VIEW public.comments_time_summary;
$$);
