import en from './json/en.json';
import fr from './json/fr.json';
// index.ts

export const defaultLocale: string = 'en';
export const languages: Record<string, any> = {
  en,
  fr
};
