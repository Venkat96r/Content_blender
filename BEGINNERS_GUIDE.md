# Beginner's Guide to XML Schemas
## Understanding Your Content Repurposing System

This guide explains the **simplified** XML schemas for your project in plain English.

---

## 📚 What Are We Building?

A system with two parts:
1. **CBank** - A library where you store content blocks (like Lego pieces)
2. **CBlend** - A workspace where you combine blocks to create new content

Think of it like:
- CBank = Your ingredients in the fridge
- CBlend = Your recipe using those ingredients

---

## 🏦 Part 1: CBank (Content Storage)

### The Big Picture

```
CBank (the library)
  │
  ├─ ContentBlock #1 (text)
  ├─ ContentBlock #2 (image)
  ├─ ContentBlock #3 (data)
  └─ ContentBlock #4 (text)
```

### CBank Structure

```xml
<CBank id="CBANK001" name="My Content Library">
    <ContentBlock>...</ContentBlock>
    <ContentBlock>...</ContentBlock>
    <ContentBlock>...</ContentBlock>
</CBank>
```

**Required attributes:**
- `id` - Unique identifier (like "CBANK001")
- `name` - Human-readable name (like "My Content Library")

### ContentBlock Structure

Each ContentBlock has:

```xml
<ContentBlock id="CB001" type="text">
    <Title>Welcome Message</Title>
    <Author>John Smith</Author>
    <CreatedDate>2026-02-15</CreatedDate>
    <Tags>
        <Tag>welcome</Tag>
        <Tag>introduction</Tag>
    </Tags>
    <Content>
        <Text>Your content here...</Text>
    </Content>
</ContentBlock>
```

**Breaking it down:**

| Element | Required? | What it is | Example |
|---------|-----------|------------|---------|
| `Title` | ✅ Yes | Name of the content | "Welcome Message" |
| `Author` | ✅ Yes | Who created it | "John Smith" |
| `CreatedDate` | ✅ Yes | When it was made | 2026-02-15 |
| `Tags` | ❌ No | Keywords for searching | welcome, intro |
| `Content` | ✅ Yes | The actual content | Text, Image, or Data |

**Attributes:**
- `id` - Unique ID like "CB001", "CB002"
- `type` - Must be: `text`, `image`, or `data`

### Content Types

You can store **3 types** of content:

#### 1. Text Content
```xml
<Content>
    <Text>This is my text content. It can be as long as you want!</Text>
</Content>
```

#### 2. Image Content
```xml
<Content>
    <Image>
        <URL>https://example.com/image.png</URL>
        <AltText>Description of the image</AltText>
    </Image>
</Content>
```

#### 3. Data Content (JSON format)
```xml
<Content>
    <Data>
        {
            "users": "10,000+",
            "satisfaction": "98%"
        }
    </Data>
</Content>
```

### Complete Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CBank xmlns="http://contentrepurpose.com/cbank"
       id="CBANK001"
       name="Marketing Content">

    <!-- Text block -->
    <ContentBlock id="CB001" type="text">
        <Title>Product Introduction</Title>
        <Author>Marketing Team</Author>
        <CreatedDate>2026-02-15</CreatedDate>
        <Tags>
            <Tag>product</Tag>
            <Tag>intro</Tag>
        </Tags>
        <Content>
            <Text>Welcome to our amazing product!</Text>
        </Content>
    </ContentBlock>

    <!-- Image block -->
    <ContentBlock id="CB002" type="image">
        <Title>Product Screenshot</Title>
        <Author>Design Team</Author>
        <CreatedDate>2026-02-15</CreatedDate>
        <Tags>
            <Tag>screenshot</Tag>
        </Tags>
        <Content>
            <Image>
                <URL>https://example.com/product.png</URL>
                <AltText>Product dashboard view</AltText>
            </Image>
        </Content>
    </ContentBlock>

</CBank>
```

---

## 🎨 Part 2: CBlend (Content Mixing)

### The Big Picture

```
CBlend (the recipe)
  │
  ├─ Name: "Welcome Blog Post"
  ├─ Target: Blog
  │
  ├─ Selected Blocks:
  │   ├─ Block CB001 (position 1)
  │   ├─ Block CB002 (position 2)
  │   └─ Block CB004 (position 3)
  │
  └─ Modifications:
      ├─ Made tone professional
      └─ Expanded content
```

### CBlend Structure

```xml
<CBlend id="BL001" status="draft">
    <n>My Blog Post</n>
    <Purpose>Introduce our product</Purpose>
    <CreatedBy>Marketing Team</CreatedBy>
    <CreatedDate>2026-02-15</CreatedDate>
    <TargetPlatform>blog</TargetPlatform>
    
    <SelectedBlocks>
        <!-- Which blocks to use -->
    </SelectedBlocks>
    
    <Modifications>
        <!-- What changes to make -->
    </Modifications>
</CBlend>
```

**Breaking it down:**

| Element | Required? | What it is |
|---------|-----------|------------|
| `Name` | ✅ Yes | Title of your blend |
| `Purpose` | ❌ No | Why you're creating this |
| `CreatedBy` | ✅ Yes | Who made it |
| `CreatedDate` | ✅ Yes | When it was made |
| `TargetPlatform` | ❌ No | Where it will be published |
| `SelectedBlocks` | ✅ Yes | Which content blocks to use |
| `Modifications` | ❌ No | Changes you made |

**Attributes:**
- `id` - Unique ID like "BL001"
- `status` - Can be: `draft`, `in-progress`, or `completed`

### TargetPlatform Options

You can publish to:
- `blog` - Blog post
- `social-media` - Facebook, Twitter, LinkedIn
- `email` - Email newsletter
- `presentation` - PowerPoint, slides

### SelectedBlocks

This tells the system which content blocks to use and in what order:

```xml
<SelectedBlocks>
    
    <!-- First block -->
    <BlockReference blockId="CB001">
        <Position>1</Position>
        <Notes>Use as introduction</Notes>
    </BlockReference>
    
    <!-- Second block -->
    <BlockReference blockId="CB002">
        <Position>2</Position>
        <Notes>Add image here</Notes>
    </BlockReference>
    
    <!-- Third block -->
    <BlockReference blockId="CB003">
        <Position>3</Position>
        <Notes>End with statistics</Notes>
    </BlockReference>
    
</SelectedBlocks>
```

**Each BlockReference has:**
- `blockId` (attribute) - Which block from CBank (like "CB001")
- `Position` - Where it goes (1, 2, 3, etc.)
- `Notes` - Optional reminder to yourself

### Modifications

Track changes you made to the content:

```xml
<Modifications>
    
    <Modification id="MOD001">
        <Type>tone-change</Type>
        <Description>Made it more professional</Description>
        <AppliedDate>2026-02-15</AppliedDate>
    </Modification>
    
    <Modification id="MOD002">
        <Type>expand</Type>
        <Description>Added more details</Description>
        <AppliedDate>2026-02-15</AppliedDate>
    </Modification>
    
</Modifications>
```

**Modification Types you can use:**
- `tone-change` - Change how it sounds (formal, casual, etc.)
- `expand` - Make it longer with more details
- `summarize` - Make it shorter
- `translate` - Change language
- `reformat` - Change the format (bullets, paragraphs, etc.)

### Complete Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CBlend xmlns="http://contentrepurpose.com/cblend"
        id="BL001"
        status="completed">

    <n>Product Launch Blog Post</n>
    <Purpose>Announce our new product to customers</Purpose>
    <CreatedBy>Sarah Johnson</CreatedBy>
    <CreatedDate>2026-02-15</CreatedDate>
    <TargetPlatform>blog</TargetPlatform>

    <SelectedBlocks>
        <BlockReference blockId="CB001">
            <Position>1</Position>
            <Notes>Introduction paragraph</Notes>
        </BlockReference>
        
        <BlockReference blockId="CB002">
            <Position>2</Position>
            <Notes>Product screenshot</Notes>
        </BlockReference>
        
        <BlockReference blockId="CB004">
            <Position>3</Position>
            <Notes>Customer testimonial</Notes>
        </BlockReference>
    </SelectedBlocks>

    <Modifications>
        <Modification id="MOD001">
            <Type>tone-change</Type>
            <Description>Made tone enthusiastic and professional</Description>
            <AppliedDate>2026-02-15</AppliedDate>
        </Modification>
    </Modifications>

</CBlend>
```

---

## 🎯 Quick Reference

### CBank Checklist

To create a valid CBank XML:
- [ ] Has `<CBank>` root element
- [ ] Has `id` and `name` attributes
- [ ] Each `<ContentBlock>` has:
  - [ ] Unique `id` attribute
  - [ ] `type` attribute (text/image/data)
  - [ ] `<Title>`, `<Author>`, `<CreatedDate>`
  - [ ] `<Content>` with Text, Image, or Data

### CBlend Checklist

To create a valid CBlend XML:
- [ ] Has `<CBlend>` root element
- [ ] Has `id` and `status` attributes
- [ ] Has `<n>`, `<CreatedBy>`, `<CreatedDate>`
- [ ] Has `<SelectedBlocks>` with at least one block
- [ ] Each `<BlockReference>` has:
  - [ ] `blockId` attribute
  - [ ] `<Position>` element

---

## 💡 Common Patterns

### Pattern 1: Simple Text-Only CBank
```xml
<CBank id="CBANK001" name="Blog Posts">
    <ContentBlock id="CB001" type="text">
        <Title>Post 1</Title>
        <Author>Me</Author>
        <CreatedDate>2026-02-15</CreatedDate>
        <Content>
            <Text>Content here</Text>
        </Content>
    </ContentBlock>
</CBank>
```

### Pattern 2: Mixed Content CBank
```xml
<CBank id="CBANK001" name="Mixed Content">
    <!-- Text -->
    <ContentBlock id="CB001" type="text">...</ContentBlock>
    <!-- Image -->
    <ContentBlock id="CB002" type="image">...</ContentBlock>
    <!-- Data -->
    <ContentBlock id="CB003" type="data">...</ContentBlock>
</CBank>
```

### Pattern 3: Simple Blend (No Modifications)
```xml
<CBlend id="BL001" status="draft">
    <n>Quick Post</n>
    <CreatedBy>Me</CreatedBy>
    <CreatedDate>2026-02-15</CreatedDate>
    
    <SelectedBlocks>
        <BlockReference blockId="CB001">
            <Position>1</Position>
        </BlockReference>
    </SelectedBlocks>
</CBlend>
```

### Pattern 4: Complex Blend (With Modifications)
```xml
<CBlend id="BL001" status="completed">
    <n>Polished Article</n>
    <Purpose>Professional blog post</Purpose>
    <CreatedBy>Team</CreatedBy>
    <CreatedDate>2026-02-15</CreatedDate>
    <TargetPlatform>blog</TargetPlatform>
    
    <SelectedBlocks>
        <BlockReference blockId="CB001">
            <Position>1</Position>
            <Notes>Intro</Notes>
        </BlockReference>
        <BlockReference blockId="CB002">
            <Position>2</Position>
            <Notes>Visual</Notes>
        </BlockReference>
    </SelectedBlocks>
    
    <Modifications>
        <Modification id="MOD001">
            <Type>tone-change</Type>
            <Description>Professional</Description>
            <AppliedDate>2026-02-15</AppliedDate>
        </Modification>
    </Modifications>
</CBlend>
```

---

## 🚫 Common Mistakes to Avoid

### ❌ Wrong: Missing required attributes
```xml
<CBank name="My Bank">  <!-- Missing id attribute! -->
```

### ✅ Right: All required attributes
```xml
<CBank id="CBANK001" name="My Bank">
```

---

### ❌ Wrong: Type doesn't match content
```xml
<ContentBlock id="CB001" type="text">  <!-- Says text -->
    <Content>
        <Image>...</Image>  <!-- But has image! -->
    </Content>
</ContentBlock>
```

### ✅ Right: Type matches content
```xml
<ContentBlock id="CB001" type="image">
    <Content>
        <Image>...</Image>
    </Content>
</ContentBlock>
```

---

### ❌ Wrong: Invalid date format
```xml
<CreatedDate>02/15/2026</CreatedDate>  <!-- Wrong format! -->
```

### ✅ Right: ISO date format (YYYY-MM-DD)
```xml
<CreatedDate>2026-02-15</CreatedDate>
```

---

### ❌ Wrong: Invalid modification type
```xml
<Type>make-better</Type>  <!-- Not a valid type! -->
```

### ✅ Right: Use valid modification types
```xml
<Type>tone-change</Type>  <!-- Valid! -->
```

---

## 🔍 Validation

To check if your XML is valid:

### Option 1: Online Validator
1. Go to: https://www.freeformatter.com/xml-validator-xsd.html
2. Paste your XSD schema
3. Paste your XML file
4. Click "Validate"

### Option 2: Command Line (xmllint)
```bash
xmllint --schema cbank_schema_simple.xsd cbank_example_simple.xml --noout
```

### Option 3: VS Code
1. Install "XML" extension by Red Hat
2. Open your XML file
3. Errors will show in red

---

## 📝 Tips for Success

1. **Start Simple**
   - Create one ContentBlock first
   - Test it validates
   - Then add more

2. **Use Comments**
   ```xml
   <!-- This is a comment explaining what I'm doing -->
   ```

3. **Keep IDs Consistent**
   - CBank: CBANK001, CBANK002
   - ContentBlocks: CB001, CB002, CB003
   - Blends: BL001, BL002
   - Modifications: MOD001, MOD002

4. **Test Each Part**
   - Validate CBank XML first
   - Then create CBlend that references it
   - Don't build everything at once

5. **Read Error Messages**
   - Validators tell you exactly what's wrong
   - Common issues: missing attributes, wrong order, typos

---

## 🎓 Next Steps

Now that you understand the schemas:

1. **Create your first CBank XML**
   - Start with 2-3 simple ContentBlocks
   - Validate it

2. **Create your first CBlend XML**
   - Reference the blocks from your CBank
   - Keep it simple at first

3. **Build your application**
   - Use the prototype provided
   - Modify it to work with these simplified schemas

4. **Extend as needed**
   - Once comfortable, you can add more features
   - The schemas are designed to be extended

---

## 📚 Complete Minimal Example

Here's the absolute minimum valid XML for each:

### Minimal CBank
```xml
<?xml version="1.0" encoding="UTF-8"?>
<CBank xmlns="http://contentrepurpose.com/cbank"
       id="CB1" 
       name="Test">
    <ContentBlock id="B1" type="text">
        <Title>Test</Title>
        <Author>Me</Author>
        <CreatedDate>2026-02-15</CreatedDate>
        <Content>
            <Text>Hello</Text>
        </Content>
    </ContentBlock>
</CBank>
```

### Minimal CBlend
```xml
<?xml version="1.0" encoding="UTF-8"?>
<CBlend xmlns="http://contentrepurpose.com/cblend"
        id="BL1" 
        status="draft">
    <n>Test</n>
    <CreatedBy>Me</CreatedBy>
    <CreatedDate>2026-02-15</CreatedDate>
    <SelectedBlocks>
        <BlockReference blockId="B1">
            <Position>1</Position>
        </BlockReference>
    </SelectedBlocks>
</CBlend>
```

---

**Good luck with your project! 🚀**

Remember: Start simple, validate often, and build up gradually!
