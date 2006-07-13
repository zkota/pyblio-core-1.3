<?xml version="1.0" encoding="utf-8"?><!-- -*- nxml -*- -->

<pyblio-schema id="org.pybliographer/pubmed/0.1">
 <name>Data from PubMed</name>

 <attribute id="pmid" type="id">
  <name>PubMed unique identifier</name>
 </attribute>

 <attribute id="journal" type="text">
  <name>Journal title</name>
  <qualifiers>
    <attribute id="issn" type="id">
      <name>Journal's ISSN</name>
    </attribute>
    <attribute id="volume" type="text">
      <name>Volume</name>
    </attribute>
    <attribute id="issue" type="text">
      <name>Issue</name>
    </attribute>
    <attribute id="year" type="text">
      <name>Year</name>
    </attribute>
    <attribute id="month" type="text">
      <name>Month</name>
    </attribute>
  </qualifiers>
 </attribute>

 <attribute id="title" type="text">
  <name>Article Title</name>
 </attribute>

 <attribute id="abstract" type="text">
  <name>Abstract</name>
 </attribute>

 <attribute id="author" type="person">
  <name>Authors</name>
 </attribute>

</pyblio-schema>