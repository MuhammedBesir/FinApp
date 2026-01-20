/**
 * Form Validation Utilities
 * Comprehensive validation functions for user inputs
 */

// Email validation
export const validateEmail = (email) => {
  const errors = [];

  if (!email || email.trim() === "") {
    errors.push("E-posta adresi gereklidir");
    return { isValid: false, errors };
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    errors.push("Geçerli bir e-posta adresi giriniz");
  }

  if (email.length > 255) {
    errors.push("E-posta adresi çok uzun");
  }

  return { isValid: errors.length === 0, errors };
};

// Password validation
export const validatePassword = (password, options = {}) => {
  const {
    minLength = 8,
    requireUppercase = true,
    requireLowercase = true,
    requireNumber = true,
    requireSpecial = false,
  } = options;

  const errors = [];

  if (!password) {
    errors.push("Şifre gereklidir");
    return { isValid: false, errors, strength: 0 };
  }

  if (password.length < minLength) {
    errors.push(`Şifre en az ${minLength} karakter olmalıdır`);
  }

  if (requireUppercase && !/[A-Z]/.test(password)) {
    errors.push("Şifre en az bir büyük harf içermelidir");
  }

  if (requireLowercase && !/[a-z]/.test(password)) {
    errors.push("Şifre en az bir küçük harf içermelidir");
  }

  if (requireNumber && !/\d/.test(password)) {
    errors.push("Şifre en az bir rakam içermelidir");
  }

  if (requireSpecial && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push("Şifre en az bir özel karakter içermelidir");
  }

  // Calculate password strength (0-100)
  let strength = 0;
  if (password.length >= 8) strength += 20;
  if (password.length >= 12) strength += 10;
  if (/[A-Z]/.test(password)) strength += 20;
  if (/[a-z]/.test(password)) strength += 15;
  if (/\d/.test(password)) strength += 20;
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength += 15;

  return {
    isValid: errors.length === 0,
    errors,
    strength: Math.min(strength, 100),
  };
};

// Username validation
export const validateUsername = (username) => {
  const errors = [];

  if (!username || username.trim() === "") {
    errors.push("Kullanıcı adı gereklidir");
    return { isValid: false, errors };
  }

  if (username.length < 3) {
    errors.push("Kullanıcı adı en az 3 karakter olmalıdır");
  }

  if (username.length > 30) {
    errors.push("Kullanıcı adı en fazla 30 karakter olabilir");
  }

  if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    errors.push("Kullanıcı adı sadece harf, rakam ve alt çizgi içerebilir");
  }

  if (/^\d/.test(username)) {
    errors.push("Kullanıcı adı rakam ile başlayamaz");
  }

  return { isValid: errors.length === 0, errors };
};

// Phone number validation (Turkish format)
export const validatePhone = (phone) => {
  const errors = [];

  if (!phone || phone.trim() === "") {
    return { isValid: true, errors }; // Phone is optional
  }

  // Remove spaces and dashes
  const cleanPhone = phone.replace(/[\s-]/g, "");

  // Turkish phone format: 05XX XXX XX XX or +90 5XX XXX XX XX
  const phoneRegex = /^(\+90|0)?5\d{9}$/;

  if (!phoneRegex.test(cleanPhone)) {
    errors.push("Geçerli bir telefon numarası giriniz (05XX XXX XX XX)");
  }

  return { isValid: errors.length === 0, errors };
};

// Number validation
export const validateNumber = (value, options = {}) => {
  const {
    min = -Infinity,
    max = Infinity,
    integer = false,
    positive = false,
    fieldName = "Değer",
  } = options;

  const errors = [];

  if (value === "" || value === null || value === undefined) {
    errors.push(`${fieldName} gereklidir`);
    return { isValid: false, errors };
  }

  const num = Number(value);

  if (isNaN(num)) {
    errors.push(`${fieldName} geçerli bir sayı olmalıdır`);
    return { isValid: false, errors };
  }

  if (integer && !Number.isInteger(num)) {
    errors.push(`${fieldName} tam sayı olmalıdır`);
  }

  if (positive && num <= 0) {
    errors.push(`${fieldName} pozitif olmalıdır`);
  }

  if (num < min) {
    errors.push(`${fieldName} en az ${min} olmalıdır`);
  }

  if (num > max) {
    errors.push(`${fieldName} en fazla ${max} olabilir`);
  }

  return { isValid: errors.length === 0, errors };
};

// Stock ticker validation
export const validateTicker = (ticker) => {
  const errors = [];

  if (!ticker || ticker.trim() === "") {
    errors.push("Hisse kodu gereklidir");
    return { isValid: false, errors };
  }

  // BIST format: XXXXX.IS (1-5 letters + .IS)
  const tickerRegex = /^[A-Z]{1,5}(\.IS)?$/i;

  if (!tickerRegex.test(ticker)) {
    errors.push("Geçerli bir BIST hisse kodu giriniz (örn: THYAO.IS)");
  }

  return { isValid: errors.length === 0, errors };
};

// Amount/Price validation for trading
export const validateTradeAmount = (amount, options = {}) => {
  const { min = 0, max = 1000000000, fieldName = "Miktar" } = options;

  const errors = [];

  if (amount === "" || amount === null || amount === undefined) {
    errors.push(`${fieldName} gereklidir`);
    return { isValid: false, errors };
  }

  const num = parseFloat(amount);

  if (isNaN(num)) {
    errors.push(`${fieldName} geçerli bir sayı olmalıdır`);
    return { isValid: false, errors };
  }

  if (num <= min) {
    errors.push(`${fieldName} ${min}'dan büyük olmalıdır`);
  }

  if (num > max) {
    errors.push(`${fieldName} çok yüksek`);
  }

  // Check decimal places (max 2 for currency)
  if (String(num).includes(".") && String(num).split(".")[1].length > 2) {
    errors.push(`${fieldName} en fazla 2 ondalık basamak içerebilir`);
  }

  return { isValid: errors.length === 0, errors };
};

// Date validation
export const validateDate = (date, options = {}) => {
  const { minDate = null, maxDate = null, fieldName = "Tarih" } = options;

  const errors = [];

  if (!date) {
    errors.push(`${fieldName} gereklidir`);
    return { isValid: false, errors };
  }

  const dateObj = new Date(date);

  if (isNaN(dateObj.getTime())) {
    errors.push(`Geçerli bir ${fieldName.toLowerCase()} giriniz`);
    return { isValid: false, errors };
  }

  if (minDate && dateObj < new Date(minDate)) {
    errors.push(
      `${fieldName} ${new Date(minDate).toLocaleDateString("tr-TR")} tarihinden sonra olmalıdır`,
    );
  }

  if (maxDate && dateObj > new Date(maxDate)) {
    errors.push(
      `${fieldName} ${new Date(maxDate).toLocaleDateString("tr-TR")} tarihinden önce olmalıdır`,
    );
  }

  return { isValid: errors.length === 0, errors };
};

// Form validation helper
export const validateForm = (formData, rules) => {
  const errors = {};
  let isValid = true;

  for (const [field, fieldRules] of Object.entries(rules)) {
    const value = formData[field];
    const fieldErrors = [];

    for (const rule of fieldRules) {
      const result = rule(value);
      if (!result.isValid) {
        fieldErrors.push(...result.errors);
      }
    }

    if (fieldErrors.length > 0) {
      errors[field] = fieldErrors;
      isValid = false;
    }
  }

  return { isValid, errors };
};

// Sanitize input (prevent XSS)
export const sanitizeInput = (input) => {
  if (typeof input !== "string") return input;

  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
    .trim();
};

// Custom validation hook helper
export const createValidator = (validationFn) => {
  return (value) => validationFn(value);
};

export default {
  validateEmail,
  validatePassword,
  validateUsername,
  validatePhone,
  validateNumber,
  validateTicker,
  validateTradeAmount,
  validateDate,
  validateForm,
  sanitizeInput,
  createValidator,
};
