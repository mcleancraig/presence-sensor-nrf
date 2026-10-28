/*
 * Copyright (c) 2026 Craig McLean
 * Debug builds only: keep the system alive after a fatal error, assert or
 * abort() so the report reaches the USB log instead of the device freezing.
 */

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(debug_fatal, LOG_LEVEL_ERR);

/* Returning makes the kernel abort only the faulting thread */
void k_sys_fatal_error_handler(unsigned int reason, const struct arch_esf *esf)
{
	ARG_UNUSED(esf);
	LOG_ERR("Fatal error %u: faulting thread aborted, system kept alive for logs", reason);
}

#ifdef CONFIG_ASSERT_NO_FILE_INFO
void assert_post_action(void)
{
	LOG_ERR("Assertion failed (continuing)");
}
#else
void assert_post_action(const char *file, unsigned int line)
{
	LOG_ERR("Assertion failed at %s:%u (continuing)", file, line);
}
#endif

void _exit(int status)
{
	LOG_ERR("abort()/exit(%d) in thread '%s': aborting that thread", status,
		k_thread_name_get(k_current_get()));
	k_thread_abort(k_current_get());
	while (1) {
	}
}
