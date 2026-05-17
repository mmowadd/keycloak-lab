FROM php:8.2-apache

# intl is not in the base image; everything else SSP needs is already compiled in
RUN apt-get update && apt-get install -y --no-install-recommends \
        libicu-dev \
        unzip \
        git \
    && docker-php-ext-install intl \
    && a2enmod rewrite \
    && rm -rf /var/lib/apt/lists/*

# Composer 2 binary
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

# Install SimpleSAMLphp 2.x with all vendor dependencies
RUN composer create-project simplesamlphp/simplesamlphp:^2.3 /opt/simplesamlphp \
    --no-interaction --prefer-dist --no-dev \
    && chown -R www-data:www-data /opt/simplesamlphp

# Apache: map /simplesaml/ → SSP public/ (AllowOverride lets .htaccess route everything)
COPY apache.conf /etc/apache2/conf-available/simplesamlphp.conf
RUN a2enconf simplesamlphp

# Main config — reads credentials from environment at runtime
COPY config.php /opt/simplesamlphp/config/config.php
RUN chown www-data:www-data /opt/simplesamlphp/config/config.php

ENV SSP_ADMIN_PASSWORD=admin123 \
    SSP_SECRET_SALT=needstobeatleast32randomchars000 \
    SSP_BASEURLPATH=/simplesaml/

EXPOSE 80
CMD ["apache2-foreground"]
