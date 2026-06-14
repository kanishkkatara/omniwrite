export enum BrandVoice {
  Authoritative = "authoritative",
  Conversational = "conversational",
  Witty = "witty",
  Empathetic = "empathetic",
  Bold = "bold",
  Educational = "educational",
  Inspirational = "inspirational",
  Professional = "professional",
  Casual = "casual",
  Humorous = "humorous",
}

export enum WritingPerspective {
  FirstPersonSingular = "first_person_singular",
  FirstPersonPlural = "first_person_plural",
  SecondPerson = "second_person",
  ThirdPerson = "third_person",
}

export enum Industry {
  Technology = "technology",
  Healthcare = "healthcare",
  Finance = "finance",
  Education = "education",
  Ecommerce = "ecommerce",
  Marketing = "marketing",
  SaaS = "saas",
  Media = "media",
  Consulting = "consulting",
  Retail = "retail",
  Manufacturing = "manufacturing",
  RealEstate = "real_estate",
  Nonprofit = "nonprofit",
  Legal = "legal",
  Other = "other",
}

export interface BrandProfile {
  id: string;
  name: string;
  tagline?: string;
  industry?: Industry;
  target_audience?: string[];
  brand_voice?: BrandVoice[];
  writing_perspective?: WritingPerspective;
  competitor_brands?: string[];
  avoid_topics?: string[];
  sample_content?: string;
  website_url?: string;
  custom_instructions?: string;
  created_at: string;
  updated_at: string;
}

export interface BrandProfileCreate {
  name: string;
  tagline?: string;
  industry?: Industry;
  target_audience?: string[];
  brand_voice?: BrandVoice[];
  writing_perspective?: WritingPerspective;
  competitor_brands?: string[];
  avoid_topics?: string[];
  sample_content?: string;
  website_url?: string;
  custom_instructions?: string;
}

export type BrandProfileUpdate = Partial<BrandProfileCreate>;
