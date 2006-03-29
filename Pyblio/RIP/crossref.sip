<?xml version="1.0" encoding="utf-8"?><!-- -*- nxml -*- -->

<pyblio-schema id="org.pybliographer/crossref/0.1">
 <name>Exchange information with http://crossref.org/</name>

 <txo-group id="doctype">
   <txo-item id="1">
     <name lang="C">article</name>
   </txo-item>
   <txo-item id="2">
     <name lang="C">book</name>
   </txo-item>
 </txo-group>

 <attribute id="doctype" type="txo" group="doctype">
  <name>Document Type</name>
 </attribute>

 <attribute id="doi" type="id">
   <name>DOI</name>
 </attribute>

 <attribute id="issn" type="id">
   <name>ISSN</name>
 </attribute>

 <attribute id="title" type="text">
   <name>Title</name>
 </attribute>

 <attribute id="serial" type="text">
   <name>Serial Title for books</name>
 </attribute>

 <attribute id="edition" type="text">
   <name>Edition Number for books</name>
 </attribute>

 <attribute id="author" type="person">
   <name>First author</name>
 </attribute>

 <attribute id="volume" type="text">
   <name>Volume</name>
 </attribute>

 <attribute id="issue" type="text">
   <name>Journal's issue</name>
 </attribute>

 <attribute id="startpage" type="text">
   <name>Start page</name>
 </attribute>

 <attribute id="part" type="text">
   <name>Part name</name>
 </attribute>

 <attribute id="year" type="date">
   <name>Publication year</name>
 </attribute>

</pyblio-schema>