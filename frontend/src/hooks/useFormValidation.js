/**
 * useFormValidation Hook
 * Reusable form validation hook with real-time validation
 */
import { useState, useCallback, useMemo } from "react";
import {
  validateEmail,
  validatePassword,
  validateUsername,
  validatePhone,
  validateNumber,
  validateTicker,
  validateTradeAmount,
  sanitizeInput,
} from "../utils/validation";

// Validation rule types
const VALIDATORS = {
  email: validateEmail,
  password: validatePassword,
  username: validateUsername,
  phone: validatePhone,
  number: validateNumber,
  ticker: validateTicker,
  amount: validateTradeAmount,
  required: (value) => ({
    isValid: value !== "" && value !== null && value !== undefined,
    errors: value ? [] : ["Bu alan zorunludur"],
  }),
  custom: (value, customFn) => customFn(value),
};

/**
 * Form validation hook
 * @param {Object} initialValues - Initial form values
 * @param {Object} validationRules - Validation rules for each field
 * @param {Object} options - Additional options
 */
export const useFormValidation = (
  initialValues = {},
  validationRules = {},
  options = {},
) => {
  const {
    validateOnChange = true,
    validateOnBlur = true,
    sanitize = true,
  } = options;

  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Validate a single field
  const validateField = useCallback(
    (name, value) => {
      const rules = validationRules[name];
      if (!rules) return { isValid: true, errors: [] };

      const fieldErrors = [];

      for (const rule of rules) {
        let result;

        if (typeof rule === "string") {
          // Built-in validator
          const validator = VALIDATORS[rule];
          if (validator) {
            result = validator(value);
          }
        } else if (typeof rule === "function") {
          // Custom validator function
          result = rule(value);
        } else if (typeof rule === "object") {
          // Validator with options
          const { type, ...ruleOptions } = rule;
          const validator = VALIDATORS[type];
          if (validator) {
            result = validator(value, ruleOptions);
          }
        }

        if (result && !result.isValid) {
          fieldErrors.push(...result.errors);
        }
      }

      return {
        isValid: fieldErrors.length === 0,
        errors: fieldErrors,
      };
    },
    [validationRules],
  );

  // Validate all fields
  const validateAll = useCallback(() => {
    const newErrors = {};
    let isValid = true;

    for (const [name, value] of Object.entries(values)) {
      const result = validateField(name, value);
      if (!result.isValid) {
        newErrors[name] = result.errors;
        isValid = false;
      }
    }

    setErrors(newErrors);
    return isValid;
  }, [values, validateField]);

  // Handle input change
  const handleChange = useCallback(
    (e) => {
      const { name, value, type, checked } = e.target;
      let newValue = type === "checkbox" ? checked : value;

      // Sanitize input if enabled
      if (sanitize && typeof newValue === "string") {
        newValue = sanitizeInput(newValue);
      }

      setValues((prev) => ({ ...prev, [name]: newValue }));

      // Validate on change if enabled
      if (validateOnChange && touched[name]) {
        const result = validateField(name, newValue);
        setErrors((prev) => ({
          ...prev,
          [name]: result.errors.length > 0 ? result.errors : undefined,
        }));
      }
    },
    [validateOnChange, touched, validateField, sanitize],
  );

  // Handle input blur
  const handleBlur = useCallback(
    (e) => {
      const { name, value } = e.target;
      setTouched((prev) => ({ ...prev, [name]: true }));

      // Validate on blur if enabled
      if (validateOnBlur) {
        const result = validateField(name, value);
        setErrors((prev) => ({
          ...prev,
          [name]: result.errors.length > 0 ? result.errors : undefined,
        }));
      }
    },
    [validateOnBlur, validateField],
  );

  // Set field value programmatically
  const setValue = useCallback((name, value) => {
    setValues((prev) => ({ ...prev, [name]: value }));
  }, []);

  // Set field error programmatically
  const setError = useCallback((name, error) => {
    setErrors((prev) => ({ ...prev, [name]: error ? [error] : undefined }));
  }, []);

  // Clear all errors
  const clearErrors = useCallback(() => {
    setErrors({});
  }, []);

  // Reset form
  const resetForm = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
  }, [initialValues]);

  // Handle form submission
  const handleSubmit = useCallback(
    (onSubmit) => async (e) => {
      e?.preventDefault();
      setIsSubmitting(true);

      // Mark all fields as touched
      const allTouched = Object.keys(values).reduce(
        (acc, key) => ({ ...acc, [key]: true }),
        {},
      );
      setTouched(allTouched);

      // Validate all fields
      const isValid = validateAll();

      if (isValid && onSubmit) {
        try {
          await onSubmit(values);
        } catch (error) {
          console.error("Form submission error:", error);
        }
      }

      setIsSubmitting(false);
    },
    [values, validateAll],
  );

  // Check if form is valid
  const isValid = useMemo(() => {
    return Object.keys(errors).every(
      (key) => !errors[key] || errors[key].length === 0,
    );
  }, [errors]);

  // Check if form is dirty (has changes)
  const isDirty = useMemo(() => {
    return JSON.stringify(values) !== JSON.stringify(initialValues);
  }, [values, initialValues]);

  // Get field props helper
  const getFieldProps = useCallback(
    (name) => ({
      name,
      value: values[name] || "",
      onChange: handleChange,
      onBlur: handleBlur,
      error: touched[name] && errors[name]?.length > 0,
      helperText: touched[name] ? errors[name]?.[0] : undefined,
    }),
    [values, errors, touched, handleChange, handleBlur],
  );

  return {
    values,
    errors,
    touched,
    isSubmitting,
    isValid,
    isDirty,
    handleChange,
    handleBlur,
    handleSubmit,
    validateField,
    validateAll,
    setValue,
    setError,
    clearErrors,
    resetForm,
    getFieldProps,
  };
};

export default useFormValidation;
