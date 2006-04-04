<?xml version="1.0" encoding="utf-8"?><!-- -*- nxml -*- -->

<pyblio-schema id="org.pybliographer/wok/0.1">
 <name>Exchange information with Web of Knowledge</name>

 <attribute id="ut" type="id">
  <name>ISI unique identifier</name>
 </attribute>

 <attribute id="doi" type="id">
  <name>DOI</name>
 </attribute>

 <attribute id="author" type="person">
   <name>Authors</name>
 </attribute>

 <attribute id="ref" type="id">
   <name>References</name>
 </attribute>

 <attribute id="abstract" type="text">
   <name>Abstract</name>
 </attribute>

 <attribute id="keyword" type="text">
   <name>Keywords</name>
 </attribute>

 <attribute id="keyword-plus" type="text">
   <name>ISI-Generated Keywords</name>
 </attribute>

 <attribute id="doctype" type="txo" group="doctype">
   <name>Document type</name>
 </attribute>

 <attribute id="source" type="text">
   <name>Source Title</name>
   <qualifiers>
     <attribute id="abbrev" type="text">
       <name>Abbreviated name</name>
     </attribute>
     <attribute id="series" type="text">
       <name>Series</name>
     </attribute>
     <attribute id="pages" type="text">
       <name>Series</name>
     </attribute>
     <attribute id="volume" type="text">
       <name>Volume</name>
     </attribute>
     <attribute id="year" type="text">
       <name>Year</name>
     </attribute>
   </qualifiers>
 </attribute>

 <attribute id="title" type="text">
   <name>Title</name>
 </attribute>


 <txo-group id="doctype">
   <txo-item id="1">
     <name lang="C">@</name>
     <name>Article</name>
   </txo-item>
   <txo-item id="2">
     <name lang="C">E</name>
     <name>Editorial Material</name>
   </txo-item>
   <txo-item id="3">
     <name lang="C">C</name>
     <name>Correction</name>
   </txo-item>
 </txo-group>

</pyblio-schema>