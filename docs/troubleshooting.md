# Troubleshooting

## Nothing is found

- Check the depth. At depth 0 only the page you entered is read; most sites
  list files one or two clicks deep.
- Make sure the right file types are ticked, and that the name patterns are
  not too narrow (`*report*` will not match `summary.pdf`).
- The site may build its links with JavaScript. The crawler reads the HTML the
  server sends and does not run scripts, so those links are invisible to it.
