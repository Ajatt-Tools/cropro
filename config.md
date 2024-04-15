<h2>Cross-Profile Search and Import</h2>

<p>
<i>Anki needs to be restarted after changing the config file directly.</i>
</p>

<h3>List of options</h3>

<details>
    <summary>General</summary>
    <ul>
        <li><code>max_displayed_notes</code> | how many search result to display on one page</li>
        <li><code>hidden_fields</code> | contents of fields that contain these keywords won't be shown.</li>
        <li><code>skip_duplicates</code> | Skips cards, which are already existent in the collection</li>
        <li><code>copy_tags</code> | Adds the category in case of web search and tags in all cases as anki tags</li>
        <li><code>search_online</code> | Toggle between local profile's and immersion kit's search</li>
        <li><code>show_note_preview</code> | Toggles the preview on the right side when having a card selected</li>
    </ul>
</details>

<details>
    <summary>Local Search</summary>
    <ul>
        <li><code>allow_empty_search</code> | Search notes even if the search field is emtpy. Will show EVERY card you got (very slow)</li>
        <li><code>copy_card_data</code> | Copies data like due date</li>
        <li><code>exported_tag</code> | Tag added to other profile's cards when imported</li>
    </ul>
</details>

<details>
<summary>High level settings</summary>
    <ul>
        <li><code>timeout_seconds</code> | How many seconds should we try to find cards online before giving up</li>
        <li><code>enable_debug_log</code> | print debug information to <code>stdout</code> and to a log file.<br/>
    Location: <code>~/.local/share/Anki2/subsearch_debug.log</code> (GNU systems) or <code>%APPDATA%/Anki2/subsearch_debug.log</code> (Windows).</li>
        <li><code>call_add_cards_hook</code> | Calls the <code>add_cards_did_add_note</code> hook as soon as a note is imported.<br/>
    For addon evaluation purposes. (<a href="https://ankiweb.net/shared/info/1207537045">example</a>)</li>
    </ul>
</details>

<p>If you enjoy this add-on, please consider supporting my work by
<b><a href="https://tatsumoto.neocities.org/blog/donating-to-tatsumoto.html">making a donation</a></b>.
Thank you so much!
</p>
