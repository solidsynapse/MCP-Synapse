<script>
  let { value = $bindable(""), class: className = "", ...rest } = $props();

  const base =
    "flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-50 dark:placeholder:text-slate-500 ring-offset-white dark:ring-offset-slate-950";

  const classes = $derived(() => [base, className].filter(Boolean).join(" "));
</script>

<input bind:value class={classes} {...rest} />
