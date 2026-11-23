# Iranian banking snapshot

Reviewed on 2026-11-14. `iran.json` contains domestic Iranian bank references,
the central bank, and former banks/credit institutions retained for historical
lookups. It includes the complete domestic roster in the CBI categories below;
foreign correspondent banks and their overseas branches are outside this seed.

## Sources

- Bank codes, Persian names and six-digit card prefixes are derived from
  [go-persian-tools](https://github.com/amiranmanesh/go-persian-tools/tree/4575d3a71f66c36da54eabb3e815464ec24086d4/bank),
  pinned at `4575d3a71f66c36da54eabb3e815464ec24086d4`.
  The source's MIT license is preserved in [banks.LICENSE](banks.LICENSE).
- Logo URLs and the two eight-digit Blu prefixes are derived from
  [IranianBanks](https://github.com/mehrnet/IranianBanks/tree/eaaa56ee8a9a777271bc375df100182aab44558d),
  pinned at `eaaa56ee8a9a777271bc375df100182aab44558d`.
  Its MIT license is preserved in [logos.LICENSE](logos.LICENSE).
- Coverage is checked against the CBI lists of
  [commercial state banks](https://www.cbi.ir/simplelist/3088.aspx),
  [specialized state banks](https://www.cbi.ir/simplelist/2389.aspx),
  [private banks](https://www.cbi.ir/simplelist/2390.aspx),
  [interest-free banks](https://www.cbi.ir/simplelist/7054.aspx),
  [bi-national banks](https://www.cbi.ir/simplelist/15166.aspx), and
  [credit institutions](https://www.cbi.ir/simplelist/3090.aspx).
- Historical `606737` (Mehr Eqtesad) is also listed in
  [IRBankNameCardNumber](https://github.com/dashti011/IRBankNameCardNumber).
- Ayandeh's transfer is documented by
  [Bank Melli's official announcements](https://telegram.me/s/bankmelli_ir?after=9347).
  Caspian's dissolution is documented in
  [the report of the CBI announcement](https://www.tasnimnews.ir/fa/news/1402/11/18/3036144/).

## Adaptation and identity

- Bank `code` is a stable seed identity, such as `IR-017`. Its suffix is the
  institution code where known; it is not a database ID or an IBAN parser.
  Caspian uses `IR-CASPIAN` because no institution code is inferred for it.
- The duplicate Mehr Iran entry `090` is not a second bank. `IR-060` identifies
  Mehr Iran once. Industry and Mine is `011`, Cooperative Development is `022`,
  and the former Tosee credit institution is `051`; conflicting secondary
  mappings were not copied.
- Five institutions absorbed by Sepah, Ayandeh, Noor, Tosee and Caspian are
  inactive. Their historical prefixes remain attached to their original issuer
  and are inactive too; a successor relationship is not inferred or persisted.
- Neo-banks do not become duplicate bank records. Blu prefixes `62198618` and
  `62198619` point to Saman. Shared six-digit prefixes retain their bank owner.
- Banks without a sourced card prefix have an empty list. Missing logos are
  null. No prefix, logo, runtime ID or synthetic placeholder is invented.
- This is a reviewed, offline reference snapshot, not a live CBI BIN registry.
  New allocations require a reviewed snapshot update. Seed execution performs
  no network requests and inserts missing identities only, preserving admin
  edits, existing prefix ownership and unrelated records.

The third-party data and logos retain their independent licenses and rights;
Core-API's proprietary license does not replace them.
