# Refit frozen GenAI evaluations with the author implementation used in the
# numerical benchmark. Reference values are deliberately absent from this script.
suppressPackageStartupMessages(library(rankrate))
stopifnot(as.character(packageVersion("rankrate")) == "1.2.1")
args <- commandArgs(trailingOnly = TRUE)
work <- normalizePath(if (length(args)) args[[1]] else ".")
scenario <- if (length(args) >= 2L) args[[2]] else "direct"
method <- if (length(args) >= 3L) args[[3]] else "ASTAR"
stopifnot(scenario %in% c("direct", "score_derived"),
          method %in% c("FV", "Greedy", "GreedyLocal", "ASTAR"))
read_matrix <- function(name) {
  as.matrix(read.csv(file.path(work, "inputs", name), row.names = 1,
                     check.names = FALSE))
}
scores <- read_matrix("scores_reverse.csv")
ranks <- read_matrix(paste0("rankings_", scenario, ".csv"))
storage.mode(scores) <- storage.mode(ranks) <- "integer"
M <- 12L
stopifnot(identical(dim(scores), c(5L, 10L)),
          identical(dim(ranks), dim(scores)),
          identical(rownames(scores), rownames(ranks)),
          all(scores >= 0L & scores <= M),
          all(apply(ranks, 1L, function(x) identical(sort(as.integer(x)), 1:10))))
set.seed(1028L)
out <- file.path(work, "outputs", scenario, method)
dir.create(out, recursive = TRUE, showWarnings = FALSE)
warnings <- messages <- character()
started <- proc.time()[["elapsed"]]
fit <- tryCatch(withCallingHandlers(
  rankrate::fit_mb(rankings = ranks, ratings = scores, M = M, method = method),
  warning = function(w) {
    warnings <<- c(warnings, conditionMessage(w)); invokeRestart("muffleWarning")
  },
  message = function(m) {
    messages <<- c(messages, conditionMessage(m)); invokeRestart("muffleMessage")
  }), error = function(e) e)
elapsed <- proc.time()[["elapsed"]] - started
if (inherits(fit, "error")) {
  write.csv(data.frame(status = "error", error = conditionMessage(fit),
                       elapsed_seconds = elapsed), file.path(out, "status.csv"),
            row.names = FALSE)
  quit(status = 1L)
}
saveRDS(fit, file.path(out, "fit.rds"))
orders <- if (is.null(dim(fit$pi0))) matrix(fit$pi0, nrow = 1L) else fit$pi0
probabilities <- if (is.null(dim(fit$p))) matrix(fit$p, nrow = 1L) else fit$p
stopifnot(nrow(orders) == nrow(probabilities), ncol(orders) == ncol(scores),
          ncol(probabilities) == ncol(scores))
theta <- as.numeric(fit$theta)
stopifnot(length(theta) == nrow(orders), all(is.finite(theta)))
log_likelihood <- vapply(seq_len(nrow(orders)), function(k) {
  rankrate::dmb(rankings = ranks, ratings = scores,
               p = probabilities[k, ], theta = theta[[k]], M = M,
               pi0 = orders[k, ], log = TRUE)
}, numeric(1L))
stopifnot(all(is.finite(log_likelihood)))
order_table <- data.frame(solution = seq_len(nrow(orders)), orders)
names(order_table)[-1L] <- paste0("position_", seq_len(ncol(orders)))
write.csv(order_table, file.path(out, "orders.csv"), row.names = FALSE)
parameter_table <- data.frame(solution = rep(seq_len(nrow(orders)), each = ncol(scores)),
                              project = rep(colnames(scores), nrow(orders)),
                              p = as.vector(t(probabilities)))
write.csv(parameter_table, file.path(out, "parameters.csv"), row.names = FALSE)
summary <- data.frame(solution = seq_len(nrow(orders)), theta = theta,
                      log_likelihood = log_likelihood,
                      nodes = as.numeric(fit$num_nodes), elapsed_seconds = elapsed)
write.csv(summary, file.path(out, "summary.csv"), row.names = FALSE)
write.csv(data.frame(status = "completed", method = method, scenario = scenario,
                       version = as.character(packageVersion("rankrate")),
                       solutions = nrow(orders), elapsed_seconds = elapsed),
            file.path(out, "status.csv"), row.names = FALSE)
writeLines(unique(c(warnings, messages)), file.path(out, "algorithm_messages.txt"))
writeLines(capture.output(sessionInfo()), file.path(out, "sessionInfo.txt"))
cat(scenario, method, "completed; solutions", nrow(orders),
    "; seconds", elapsed, "; maximum log likelihood", max(log_likelihood), "\n")
