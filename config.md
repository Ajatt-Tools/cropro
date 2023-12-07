## Cross-Profile Search and Import

**Anki needs to be restarted after changing the config.**

### List of options:

* `max_displayed_notes` - how many search result to display
* `enable_debug_log` - print debug information to `stdout` and to a log file.
Log location: `~/.local/share/Anki2/cropro.log` (GNU systems).
* `tag_exported_cards` - tag cards in the other profile as `exported`
so that you could easily find and delete them later.
* `exported_tag` - The tag used for the above
* `hidden_fields` - contents of fields that contain these keywords won't be shown in preview.
* `skip_duplicates` - Skips the import of the card if already existing
* `copy_tags` - Copies the tags of the old note over to the new one. ! Don't confuse with `copy_card_data`
* `allow_empty_search` - Search notes even if the search field is emtpy. May be slow.
* `preview_on_right_side` - Enables or disables the preview
* `copy_card_data` - Copies the due date etc. except for tags or contents.
* `call_add_cards_hook` - Calls the `add_cards_did_add_note` hook as soon as a note
  is imported through the main CroPro window.
  For addon evaluation purposes.

---

If you enjoy this add-on, please consider supporting my work by
**[pledging your support on Patreon](https://www.patreon.com/tatsumoto_ren)**.
Thank you so much!
