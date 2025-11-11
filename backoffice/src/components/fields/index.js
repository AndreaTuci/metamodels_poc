// Export tutti i componenti field per facilitare l'importazione
import BaseField from './BaseField.vue'
import CharField from './CharField.vue'
import TextField from './TextField.vue'
import NumberField from './NumberField.vue'
import BooleanField from './BooleanField.vue'
import DateField from './DateField.vue'
import EmailField from './EmailField.vue'
import URLField from './URLField.vue'
import DynamicField from './DynamicField.vue'
import DynamicForm from './DynamicForm.vue'

// Mapping tra i tipi Django e i componenti Vue
export const fieldComponents = {
  CharField,
  TextField,
  IntegerField: NumberField,
  FloatField: NumberField,
  BooleanField,
  DateField,
  DateTimeField: DateField,
  EmailField,
  URLField
}

// Mapping per retrocompatibilità con i nomi lowercase
export const fieldComponentsLegacy = {
  char: CharField,
  text: TextField,
  integer: NumberField,
  decimal: NumberField,
  boolean: BooleanField,
  date: DateField,
  datetime: DateField,
  email: EmailField,
  url: URLField
}

// Export singoli componenti
export {
  BaseField,
  CharField,
  TextField,
  NumberField,
  BooleanField,
  DateField,
  EmailField,
  URLField,
  DynamicField,
  DynamicForm
}

// Funzione helper per ottenere il componente corretto
export function getFieldComponent(fieldType) {
  return fieldComponents[fieldType] || fieldComponents.CharField // fallback
}

// Funzione per ottenere il componente con supporto legacy
export function getFieldComponentLegacy(fieldType) {
  return fieldComponentsLegacy[fieldType] || fieldComponents[fieldType] || fieldComponents.CharField
}