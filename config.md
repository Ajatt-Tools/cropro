## Cross-Profile Search and Import

**Anki needs to be restarted after changing the config.**

### List of options:

* `enable_debug_log` - print debug information to `stdout` and to a log file.
Log location: `~/.local/share/Anki2/cropro.log` (GNU systems).
* `max_displayed_notes` - how many search result to display
* `tag_exported_cards` - tag cards in the other profile as `exported`
so that you could easily find and delete them later.
* `hidden_fields` - contents of fields that contain these keywords won't be shown.
* `allow_empty_search` - Search notes even if the search field is emtpy. May be slow.
* `call_add_cards_hook` - Calls the `add_cards_did_add_note` hook as soon as a note 
is imported through the main CroPro window.<br>For addon evaluation purposes.

---

If you enjoy this add-on, please consider supporting my work by
**[pledging your support on Patreon](https://www.patreon.com/tatsumoto_ren)**.
Thank you so much!
