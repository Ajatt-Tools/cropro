<h2>Cross-Profile Search and Import</h2>

<p>
<i>Anki needs to be restarted after changing the config file directly.</i>
</p>

<h3>List of options</h3>

<details>
    <summary>General</summary>
    <ul>
        <li><code>notes_per_page</code> | How many search results to display on one page.</li>
        <li><code>hidden_fields</code> | Hide fields whose names contain these words.</li>
        <li><code>skip_duplicates</code> | Do not import a note if it is already present in the current collection.</li>
        <li><code>copy_tags</code> | Copy tags from the original note to the imported note.</li>
        <li><code>preview_on_right_side</code> | Show a preview on the right side of the window when a note is selected.</li>
        <li><code>search_the_web</code> | Search the Internet instead of searching notes in a local profile.</li>
    </ul>
</details>

<details>
    <summary>Local Search</summary>
    <ul>
        <li><code>allow_empty_search</code> | Show notes from the other collection even when the search bar is empty.</li>
        <li><code>copy_card_data</code> | Copy scheduling information of cards created from imported notes, such as due date and interval.</li>
        <li><code>exported_tag</code> | Tag original notes in the other profile after they are imported.</li>
        <li><code>imported_tag</code> | Tag notes imported into the current collection. Leave it empty to disable tagging.</li>
        <li><code>sentence_field_name</code> | Field name used to sort local search results.</li>
    </ul>
</details>

<details>
    <summary>Web Search</summary>
    <ul>
        <li><code>sentence_min_length</code> | Minimum sentence length for web search results. Set to <code>0</code> for no limit.</li>
        <li><code>sentence_max_length</code> | Maximum sentence length for web search results. Set to <code>0</code> for no limit.</li>
        <li><code>remote_fields</code> | Field names used when creating notes from web search results.</li>
        <li><code>sentence_kanji</code> | Target field for the Japanese sentence.</li>
        <li><code>sentence_furigana</code> | Target field for the sentence with furigana.</li>
        <li><code>sentence_eng</code> | Target field for the English sentence.</li>
        <li><code>sentence_audio</code> | Target field for sentence audio.</li>
        <li><code>image</code> | Target field for the image.</li>
        <li><code>notes</code> | Target field for notes or source information.</li>
    </ul>
</details>

<details>
    <summary>High Level</summary>
    <ul>
        <li><code>timeout_seconds</code> | Give up trying to connect to the remote server after this many seconds.</li>
        <li><code>http_proxy</code> | HTTP and HTTPS proxy for web search requests, for example <code>socks5://127.0.0.1:9099</code>.</li>
        <li><code>enable_debug_log</code> | Write events related to this add-on to Anki's add-on log folder.<br/>
    Use the settings dialog's <b>Show log</b> or <b>Open folder</b> buttons to view the current log file.</li>
        <li><code>call_add_cards_hook</code> | Call the <code>add_cards_did_add_note</code> hook after a note is imported, for compatibility with other add-ons.</li>
    </ul>
</details>

<p>If you enjoy this add-on, please consider supporting my work by
<b><a href="https://tatsumoto.neocities.org/blog/donating-to-tatsumoto.html">making a donation</a></b>.
Thank you so much!
</p>
