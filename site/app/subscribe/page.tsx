'use client';
import { useState, useEffect } from 'react';

const STEPS = ['name', 'contact', 'location', 'goals', 'done'] as const;
type Step = typeof STEPS[number];

const GENDER_OPTIONS = [
  { value: 'male',        label: 'Male' },
  { value: 'female',      label: 'Female' },
  { value: 'non-binary',  label: 'Non-binary' },
  { value: 'prefer-not',  label: 'Prefer not to say' },
  { value: 'other',       label: 'Other' },
];