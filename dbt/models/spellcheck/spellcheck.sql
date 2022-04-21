with step1 as (
    select sp.resource_id
         , sp.resource_field::resource_field
         , sp.resource_type::resource_type
         , sp.text_content
         , sp.derived_at
         , sp.error -> 'language' ->> 'code'                                    lang
         , sp.error -> 'language' -> 'detectedLanguage' ->> 'code'              detected_lang
         , (sp.error -> 'language' -> 'detectedLanguage' -> 'confidence')::real detected_lang_confidence
         , jsonb_array_elements(sp.error -> 'matches')                          "match"
         , sp.error
    from {{ source('languagetool', 'spellcheck') }} sp
)

select sp.*
     , (sp.detected_lang = sp.lang)             is_lang_detected
     , (sp.detected_lang_confidence > .99)       is_high_confidence
     , sp.match -> 'rule' ->> 'id'               rule_id
     , sp.match -> 'rule' -> 'category' ->> 'id' category_id
     , sp.match -> 'rule' ->> 'issueType'        issue_type
     , sp.match -> 'type' ->> 'typeName'         type_name
     , (sp.match -> 'length')::smallint          "length"
     , (sp.match -> 'offset')::smallint          "offset"
     , sp.match -> 'context'                     context
from step1 sp
