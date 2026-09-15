# bio 服务器入口 —— 计算 /p/ 代理地址并显示（幂等，可重复执行）
local({
  basef <- path.expand("~/.rstudio-entry/base.txt")
  base <- if (file.exists(basef)) trimws(readLines(basef, n = 1)[1]) else ""
  if (!nzchar(base)) { cat("[bio-entry] 缺少 ~/.rstudio-entry/base.txt，跳过\n"); return(invisible()) }
  svc <- list(
    list("终端ttyd", 7681),
    list("仪表盘", 8899),
    list("VSCode", 8080)
  )
  out <- character(0)
  for (s in svc) {
    u <- tryCatch(as.character(rstudioapi::translateLocalUrl(sprintf("http://localhost:%d", s[[2]]))),
                  error = function(e) "")
    if (nzchar(u)) out <- c(out, sprintf("%s  %s%s", s[[1]], base, u))
  }
  if (length(out)) {
    dir <- path.expand("~/.rstudio-entry")
    dir.create(dir, showWarnings = FALSE)
    writeLines(out, file.path(dir, "urls.txt"))
    if (interactive()) {
      cat("\n== 服务器入口（浏览器需先登录 webvpn.wmu.edu.cn）==\n")
      for (l in out) cat("  ", l, "\n", sep = "")
      cat("\n")
    }
  } else {
    cat("[bio-entry] translateLocalUrl 不可用，跳过\n")
  }
})
